##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pathlib
import re
from typing import Any, List, Optional, Tuple, Union

import click
import isort
import yaml
from black import FileMode, format_str
from jinja2 import Environment, FileSystemLoader

ROOT_PATH = pathlib.Path(__file__).parent.resolve()


def format_value(value: Any) -> Union[Any, str]:
    """Add double quotes to a string if value is
    of type string. Else return original value

    :param value: value to evaluate
    :return: quotet string if value was a string
    """

    if isinstance(value, (str)):
        return f'"{value}"'

    return value


def find_string_in(
    nested_dict: dict, search_value: str, prepath: Tuple[str, ...] = ()
) -> Optional[Tuple[str, ...]]:
    """find if string is part of an value in a nested dictionary.

    :param nested_dict: dictionary to search in
    :param search_value: string to search for
    :param prepath: path storage for recursive call, defaults to ()
    :return: path to locataion when found else None
    """
    for key, value in nested_dict.items():
        path = prepath + (key,)
        if isinstance(value, str) and search_value in value:  # found value
            return path
        elif hasattr(value, "items"):
            key_path = find_string_in(value, search_value, path)
            if key_path is not None:
                return key_path
    # If not found
    return None


def nested_get(dic: dict, keys: Tuple[str, ...], copy: bool) -> Any:
    """Get dictionary items from list of keys

    :param dic: dictionary to search in
    :param keys: key path as list
    :return: element at located position
    """
    for key in keys:
        dic = dic[key]

    if copy:
        return dict(dic)

    return dic


def remove_key(dic: dict, key_path: Tuple[str, ...]) -> None:
    """Remove dictionary element at given location.

    :param dic: dictionary where the key shall be removed
    :param key_path: key path as list
    """
    for key in key_path[:-1]:
        dic = dic[key]
    del dic[key_path[-1]]


def get_imports(file: str) -> List[str]:
    """Get all "from x import y" from a python script.

    :param file: python file to read in
    :return: all from imports
    """

    return [line for line in open(file, encoding="utf8") if re.match(r"from.*$", line)]


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-d",
    "--destination",
    default="./conftest.py",
    help="Output file path.",
    show_default=True,
)
def main(filename: str, destination: str):
    """Generate files from a pykiso config to use
    pytest instead of pykiso tests.

    :param filename: pykiso yaml file to convert
    :param destination: destination file path
    """

    with open(filename, encoding="utf8") as file:

        pykiso_config = yaml.load(file, Loader=yaml.FullLoader)

    template_loader = FileSystemLoader(searchpath=str(ROOT_PATH / "templates"))
    template_env = Environment(loader=template_loader)
    template_env.filters["format_value"] = format_value
    template = template_env.get_template("conftest_template.jinja2")

    # Grap import informations -> Channels and Auxiliaries
    yaml_config_folder = pathlib.Path(filename).resolve().parent

    import_info = set()

    for _, value in pykiso_config["auxiliaries"].items():
        import_info.add(value["type"])

    for _, value in pykiso_config["connectors"].items():
        import_info.add(value["type"])

    module_imports = {}
    for aux_con_type in import_info:
        value, key = aux_con_type.split(":")
        if ".py" in value:
            ext_file_imports = get_imports(yaml_config_folder / value)
            for imp in ext_file_imports:
                _, value, _, key = imp.strip().split(" ")

        module_imports[key] = value

    # Check if we have a proxy auxiliary
    key_path = find_string_in(pykiso_config, "ProxyAuxiliary")
    proxy_aux_config = None
    if key_path:
        proxy_aux_config = nested_get(pykiso_config, key_path[:-1], copy=True)
        remove_key(pykiso_config, key_path[:-1])
        proxy_aux_config["name"] = key_path[1]

    # Use jinja to render conftest
    conftest = template.render(
        dict_item=pykiso_config,
        proxy_aux_config=proxy_aux_config,
        module_imports=module_imports,
    )

    # Sort imports with isort and use black to format the code
    conftest = format_str(isort.code(conftest), mode=FileMode())

    if not destination.endswith(".py"):
        destination += ".py"
    with open(destination, "w", encoding="utf8") as file:
        file.write(conftest)

    print(f"Conftest has been written to {destination}")


if __name__ == "__main__":
    main()
