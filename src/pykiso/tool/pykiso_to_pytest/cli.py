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
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click
import isort
from black import FileMode, format_str
from jinja2 import Environment, FileSystemLoader

from pykiso import config_parser

ROOT_PATH = pathlib.Path(__file__).parent.resolve()


def format_value(value: Any) -> Union[Any, str]:
    """Add double quotes to a string if value is
    of type string. Else return original value

    :param value: value to evaluate
    :return: quoted string if value was a string
    """

    if isinstance(value, (str)):
        return f'"{value}"'

    return value


def find_string_in(
    nested_dict: dict, search_value: str, prepath: Tuple[str, ...] = ()
) -> Optional[Tuple[str, ...]]:
    """Find if string is part of a value in a nested dictionary.

    :param nested_dict: dictionary to search in
    :param search_value: string to search for
    :param prepath: path storage for recursive call, defaults to ()
    :return: path to locataion when found else None
    """
    for key, value in nested_dict.items():
        path = prepath + (key,)
        if isinstance(value, str) and search_value in value:  # found value
            return path
        elif isinstance(value, dict):
            key_path = find_string_in(value, search_value, path)
            if key_path is not None:
                return key_path
    # If not found
    return None


def nested_get(dic: dict, keys: List[str], copy: bool = False) -> Any:
    """Get dictionary items from a sequence of keys

    :param dic: dictionary to search in
    :param keys: key path as list
    :param copy: if true return a new dictionary instance
    :return: dictionary value at located key positions
    """
    for key in keys:
        dic = dic[key]

    if copy:
        return dict(dic)

    return dic


def remove_key(dic: Dict[str, Union[Dict, Any]], key_path: List[str]) -> None:
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
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-d",
    "--destination",
    default="./conftest.py",
    help="Output file path.",
    type=click.Path(writable=True),
    show_default=True,
)
def main(filename: str, destination: str):
    """Generate files from a pykiso config to use
    pytest instead of pykiso tests.

    :param filename: pykiso yaml file to convert
    :param destination: destination file path
    """
    pykiso_config = config_parser.parse_config(filename)

    template_loader = FileSystemLoader(searchpath=str(ROOT_PATH / "templates"))
    template_env = Environment(loader=template_loader)
    template_env.filters["format_value"] = format_value
    template = template_env.get_template("conftest_template.jinja2")

    # Grab import information -> Channels and Auxiliaries
    yaml_config_folder = pathlib.Path(filename).resolve().parent

    import_info = set()

    for _, value in pykiso_config["auxiliaries"].items():
        import_info.add(value["type"])

    for _, value in pykiso_config["connectors"].items():
        import_info.add(value["type"])

    module_imports = {}
    for aux_con_type in import_info:
        value, key = aux_con_type.split(":")[-2:]
        if ".py" in value:
            ext_file_imports = get_imports(yaml_config_folder / value)
            for imp in ext_file_imports:
                _, value, _, key = imp.strip().split(" ")

        module_imports[key] = value

    # Check if we have a proxy auxiliary
    key_path = find_string_in(pykiso_config, "ProxyAuxiliary")
    proxy_aux_config = None
    if key_path:
        proxy_aux_path = list(key_path[:-1])
        proxy_aux_name = key_path[1]
        proxy_aux_config = nested_get(pykiso_config, proxy_aux_path, copy=True)
        remove_key(pykiso_config, proxy_aux_path)
        proxy_aux_config["name"] = proxy_aux_name

    # Use jinja to render conftest
    conftest = template.render(
        sys_args=sys.argv,
        dict_item=pykiso_config,
        proxy_aux_config=proxy_aux_config,
        module_imports=module_imports,
    )
    # Sort imports with isort and use black to format the code
    conftest = format_str(isort.code(conftest), mode=FileMode())

    destination_path = Path(destination)
    if destination_path.is_dir():
        destination_path = destination_path / "conftest.py"
    else:
        if not destination_path.suffix == ".py":
            destination_path = destination_path.with_suffix(".py")

    with open(destination_path, "w", encoding="utf8") as file:
        file.write(conftest)

    print(f"Conftest has been written to {destination_path.resolve()}")


if __name__ == "__main__":
    main()
