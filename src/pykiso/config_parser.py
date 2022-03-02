##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Configuration File Parser
*************************

:module: config_parser

:synopsis: Load and parse the YAML configuration file.

.. currentmodule:: config_parser


"""

import logging
import operator
import os
import re
import sys
from distutils.version import LooseVersion
from pathlib import Path
from typing import Callable, Dict, List, TextIO, Union

import pkg_resources
import yaml

from pykiso.types import PathType


def check_requirements(requirements: List[dict]):
    """Check the environment before running the tests

    :param requirements: requirements to be checked
    """
    condition_to_operator = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }
    requirement_satisfied = True
    for req in requirements:
        for package, expected_version in req.items():
            try:
                logging.debug(f"Check YAML requirements: {package}")
                current_version = pkg_resources.get_distribution(package).version
                logging.debug(f"current_version: {current_version}")

                # check if condition provided
                pattern = r"([<>=!]{1,2})"
                match = re.split(pattern, expected_version)
                if len(match) > 1:
                    # pattern found eg: match = ['', '>=', '0.1.2']
                    condition = match[1]
                    exp_version = match[2].strip()

                    try:
                        compare_operation = condition_to_operator[condition]
                        check = compare_operation(
                            LooseVersion(current_version), LooseVersion(exp_version)
                        )
                        if check is False:
                            # Version not satisfied
                            logging.error(
                                f"Requirement issue: found {package} with version '{current_version}' but '{expected_version}' given"
                            )
                    except KeyError as e:
                        # comparator invalid
                        logging.error(
                            f"Requirement issue: comparator '{e}' not among {list(condition_to_operator.keys())}"
                        )
                        check = False

                    requirement_satisfied &= check

                elif current_version != expected_version and expected_version != "any":
                    if LooseVersion(current_version) < LooseVersion(expected_version):
                        # Version not satisfied: current_version < expected_version
                        requirement_satisfied = False
                        logging.error(
                            f"Requirement issue: found {package} with version '{current_version}' instead of '{expected_version}' (minimum)"
                        )

            except pkg_resources.DistributionNotFound:
                # package not installed or misspelled
                requirement_satisfied = False
                logging.error(f"Dependency issue: {package} not found")

    if not requirement_satisfied:
        logging.error("At least one requirement is not satisfied")
        sys.exit(1)


def parse_config(fname: PathType) -> Dict:
    """Parse YAML config file.

    :param fname: path to the config file

    :return: config dict with resolved paths where needed
    """

    class YamlLoader(yaml.SafeLoader):
        """Extension of default yaml.SafeLoader that integrates
        custom !include tag management and performs config parsing
        at load time.
        """

        type_pattern = re.compile(r".*:.*")
        env_var_pattern = re.compile(r"ENV{(\w+)(=(.+))?}")
        rel_path_pattern = re.compile(r'[^\n"?:*<>|]')

        def __init__(self, stream: TextIO):
            """Initialize attributes.

            :param stream: current stream in use
            """
            self._root = Path(fname).parent
            super().__init__(stream)

        @staticmethod
        def add_implicit_constructor(
            tag: str, pattern: re.Pattern, constructor: Callable
        ) -> None:
            """Combination of add_implicit_resolver and add_constructor.

            :param tag: explicit tag that can be specified in the YAML file
            :param pattern: pattern to match to implicitly set the tag
            :param constructor: function to call when the tag is set
            """
            YamlLoader.add_implicit_resolver(tag, pattern, first=None)
            YamlLoader.add_constructor(tag, constructor)

        @staticmethod
        def is_key(node: yaml.nodes.ScalarNode) -> bool:
            print()
            print("Value", node.value)
            print("Tag", node.tag)
            end_mark: yaml.error.Mark = node.end_mark
            if end_mark.buffer is None:
                print("\n    buffer", node.end_mark.buffer)
                print("\n    column", node.end_mark.column)
                print("\n    index", node.end_mark.index)
                print("\n    line", node.end_mark.line)
                print("\n    name", node.end_mark.name)
                print("\n    pointer", node.end_mark.pointer)
                return True
            print("Test start", node.start_mark.buffer[node.start_mark.pointer])
            print("Test end", node.end_mark.buffer[node.end_mark.pointer])
            return node.end_mark.buffer[node.end_mark.pointer] == ":"


        def include(self, node: yaml.nodes.ScalarNode) -> dict:
            """Return the content of a yaml file identified by !include
            tag.

            :param node: ScalarNode currently in use

            :return: yaml file content
            """
            print("*************** INCLUDE")
            print("\n    buffer", node.end_mark.buffer)
            print("\n    column", node.end_mark.column)
            print("\n    index", node.end_mark.index)
            print("\n    line", node.end_mark.line)
            print("\n    name", node.end_mark.name)
            print("\n    pointer", node.end_mark.pointer)
            filename = (self._root / Path(node.value)).resolve()
            return yaml.load(filename.read_text(), Loader=YamlLoader)

        def resolve_path(self, node: yaml.nodes.ScalarNode) -> str:
            """Resolve a path relative to the config file's location.

            :param node: ScalarNode currently in use

            :return: the resolved config path if needed
            """

            """
            print("Start mark", node.start_mark)
            print("End mark")
            print("\n    buffer", node.end_mark.buffer)
            print("\n    column", node.end_mark.column)
            print("\n    index", node.end_mark.index)
            print("\n    line", node.end_mark.line)
            print("\n    name", node.end_mark.name)
            print("\n    pointer", node.end_mark.pointer)
            """

            if YamlLoader.is_key(node):
                return str(node.value)

            # print("ID", node.id)
            # print("Style", node.style)
            value = node.value
            config_path_unresolved = Path(value)
            if not config_path_unresolved.is_absolute():
                config_path = (self._root / config_path_unresolved).resolve()
                if config_path.exists():
                    value = config_path
                    logging.debug(
                        f"Resolved relative path {config_path_unresolved} to {value}"
                    )
            return str(value)

        def fix_types_loc(self, node: yaml.nodes.ScalarNode) -> str:
            """Parse the type field in the config file and resolves it if necessary.

            :param node: ScalarNode currently in use

            :return: config sub-dict containing the resolved type if needed
            """
            thing = node.value
            loc, _class = thing.rsplit(":", 1)
            if not loc.endswith(".py"):
                return thing
            path = Path(loc)
            if not path.is_absolute():
                path = (self._root / path).resolve()
                thing = str(path) + ":" + _class
                logging.debug(f"Resolved path : {thing}")
            return thing

        def parse_env_var(self, node: yaml.nodes.ScalarNode) -> Union[str, int]:
            """Search for an environment variable pattern in the yaml file and
            (1) try to replace it with the value of an environment variable of the same name
            (2) Assign the default value if the environment variable was not found
            (3) raise an error if 1. and 2. failed

            Additionally, cast the value if it matches an integer.

            :param node: ScalarNode currently in use

            :return: config sub-dict value with replaced environment variable if needed

            :raise: ValueError if the environment variable not found and no default value specified
            """
            if node.tag == self.DEFAULT_SCALAR_TAG:
                logging.warning(
                    "YAML warning: environment variables should not be put in quotes"
                )
            match = re.findall(self.env_var_pattern, node.value)
            # no match means the node is just a string
            if not match:
                return str(node.value)
            # Parse detected environment variable
            match_single_env = str(match[0][0])
            match_env_with_val = str(match[0][2])

            if match_single_env in os.environ:
                env = os.environ[match_single_env]
            elif match_env_with_val:
                env = match_env_with_val
            else:
                raise ValueError(
                    f"Environment variable {match_single_env} not found and no default value specified"
                )
            is_numeric = re.fullmatch(r"\d+", env)
            is_hex = re.fullmatch(r"0x[0-9a-fA-F]+", env)
            is_bool = env.lower() in ["true", "false"]
            if is_numeric is not None:
                config_element = int(env)
            elif is_hex is not None:
                config_element = int(env, base=16)
            elif is_bool:
                config_element = env.lower() == "true"
            else:
                config_element = env
            logging.debug(
                f"Replaced environment variable {match_single_env} with {config_element}"
            )

    YamlLoader.add_constructor("!include", YamlLoader.include)
    # parse quoted environment variables
    YamlLoader.add_constructor(YamlLoader.DEFAULT_SCALAR_TAG, YamlLoader.parse_env_var)
    # parse unquoted environment variables
    YamlLoader.add_implicit_constructor(
        "!env", YamlLoader.env_var_pattern, YamlLoader.parse_env_var
    )
    YamlLoader.add_implicit_constructor(
        "!type", YamlLoader.type_pattern, YamlLoader.fix_types_loc
    )
    YamlLoader.add_implicit_constructor(
        "!resolve", YamlLoader.rel_path_pattern, YamlLoader.resolve_path
    )

    cfg = yaml.load(f.read_text(), Loader=YamlLoader)

    # Check requirements
    requirements = cfg.get("requirements")
    if requirements:
        check_requirements(requirements)

    return cfg


if __name__ == "__main__":
    import json

    os.environ["TEST_SUITE_1"] = "test_suite_1"
    f = Path(__file__).resolve().parent / "nested_yaml/test.yaml"

    print(json.dumps(parse_config(f), indent=2))
