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

import ast
import io
import logging
import os
import re
import sys
import typing
from distutils.version import LooseVersion
from pathlib import Path
from typing import Callable, TextIO, Union

import pkg_resources
import yaml

from .types import PathType


def check_requirements(requirements: list):
    """Check the environment before running the tests

    :param requirements: requirements to be checked
    """
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
                    check = (
                        LooseVersion(current_version) < LooseVersion(exp_version)
                        if condition == "<"
                        else LooseVersion(current_version) <= LooseVersion(exp_version)
                        if condition == "<="
                        else LooseVersion(current_version) > LooseVersion(exp_version)
                        if condition == ">"
                        else LooseVersion(current_version) >= LooseVersion(exp_version)
                        if condition == ">="
                        else LooseVersion(current_version) == LooseVersion(exp_version)
                        if condition == "=="
                        else LooseVersion(current_version) != LooseVersion(exp_version)
                        if condition == "!="
                        else None
                    )

                    if check is False:
                        # Version not satisfied
                        logging.error(
                            f"Requirement issue: found {package} with version '{current_version}' but '{expected_version}' given"
                        )
                    elif check is None:
                        # comparator invalid
                        logging.error(
                            f"Requirement issue: comparator '{condition}' not among [<, <=, >, >=, ==, !=]"
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


def parse_config(fname: PathType) -> typing.Dict:
    """Parse YAML config file.

    :param fname: path to the config file

    :return: config dict with resolved paths where needed
    """

    class YamlLoader(yaml.SafeLoader):
        """Extension of default yaml.SafeLoader who integrates
        custom !include tag management.
        """

        def __init__(self, stream: io.TextIOWrapper):
            """Initialize attributes.

            :param stream: current stream in use
            """
            self._root = Path(fname).resolve().parent
            super().__init__(stream)

        def include(self, node: yaml.nodes.ScalarNode) -> dict:
            """Return the content of an yaml file identify by !include
            tag.

            :param node: ScalarNode currently in use

            :return: yaml file content
            """
            filename = (self._root / Path(node.value)).resolve()
            with open(filename, "r") as f:
                return yaml.load(f, Loader=YamlLoader)

    YamlLoader.add_constructor("!include", YamlLoader.include)

    with open(fname) as f:
        cfg = yaml.load(f.read(), Loader=YamlLoader)

    # fix suite-dirs
    base_dir = Path(fname).resolve().parent

    def _fix_types_loc(thing: dict) -> dict:
        """Parse the type field in the config file and resolves it if necessary.

        :param thing: config sub-dict containing the type

        :return: config sub-dict containing the resolved type if needed
        """
        loc, _class = thing["type"].rsplit(":", 1)
        if not loc.endswith(".py"):
            return thing
        path = Path(loc)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
            thing["type"] = str(path) + ":" + _class
            logging.debug(f'Resolved path : {thing["type"]}')
        return thing

    def _parse_env_var(config_element: str) -> str:
        """Search for an environment variable pattern in the yaml file and
        (1) try to replace it with the value of an environment variable of the same name
        (2) Assign the default value if the environment variable was not found
        (3) raise an error if 1. and 2. failed

        Additionally, cast the value if it matches an integer.

        :param config_element: config sub-dict value

        :return: config sub-dict value with replaced environment variable if needed

        :raise: ValueError if the environment variable not found and no default value specified
        """
        # Check for regular expression "ENV{word=.}"
        match = re.compile(r"ENV{(\w+)(=(.+))?}").findall(str(config_element))
        if match:
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
        return config_element

    def _resolve_path(config_path: str) -> str:
        """Resolve a path relative to the config file's location.

        :param config_path: a config path

        :return: the resolved config path if needed
        """
        config_path_unresolved = Path(config_path)
        if not config_path_unresolved.is_absolute():
            config_path = (base_dir / config_path_unresolved).resolve()
            logging.debug(
                f"Resolved relative path {config_path_unresolved} to {config_path}"
            )
        return str(config_path)

    def _check_path(path: str) -> bool:
        """Check if the argument is a valid path.

        :param path: any string in the config file's values

        :return: a boolean indicating if the string is a valid path
        """
        is_valid = False
        if "./" in path.replace(".\\", "./"):
            invalid_characters = (":", "*", "?", "<", ">", "|")
            is_valid = (
                False
                if (any(c in invalid_characters for c in path))
                else (Path(path).exists() or (base_dir / Path(path)).exists())
            )
        return is_valid

    def _resolve_config_paths(config: dict) -> dict:
        """Iterate over the config dict and resolve all of the config file paths.

        :param config: config dict

        :return: config dict with resolved paths
        """
        for key in config.keys():
            if isinstance(config.get(key), dict):
                _resolve_config_paths(config.get(key))
            elif isinstance(config.get(key), str):
                config[key] = _parse_env_var(config[key])
                config[key] = (
                    _resolve_path(config[key])
                    if isinstance(config[key], str) and _check_path(config[key])
                    else config[key]
                )
            elif isinstance(config.get(key), list) and key == "test_suite_list":
                for test_suite in config[key]:
                    test_suite["suite_dir"] = _resolve_path(
                        _parse_env_var(test_suite["suite_dir"])
                    )
        return config

    cfg["connectors"] = {n: _fix_types_loc(s) for n, s in cfg["connectors"].items()}
    cfg["auxiliaries"] = {n: _fix_types_loc(s) for n, s in cfg["auxiliaries"].items()}
    cfg = _resolve_config_paths(cfg)

    # Check requirements
    requirements = cfg.get("requirements")
    if requirements:
        check_requirements(requirements)

    return cfg


def _parse_config(fname: PathType) -> typing.Dict:
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
        env_var_pattern = re.compile(r"ENV{(\w+)}")
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

        def include(self, node: yaml.nodes.ScalarNode) -> dict:
            """Return the content of an yaml file identify by !include
            tag.

            :param node: ScalarNode currently in use

            :return: yaml file content
            """
            filename = self._root / Path(node.value).resolve()
            with open(filename, "r") as f:
                return yaml.load(f, Loader=YamlLoader)

        def resolve_path(self, node: yaml.nodes.ScalarNode) -> str:
            """Resolve a path relative to the config file's location.

            :param node: ScalarNode currently in use

            :return: the resolved config path if needed
            """
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
            """Search for an environment variable and replace it with the associated value.

            Additionally, cast the value if it matches a python type supported by ast.literal_eval().

            :param node: ScalarNode currently in use

            :return: config sub-dict value with replaced environment variable if needed
            """
            match = re.search(self.env_var_pattern, node.value)
            # no match means the node is just a string
            if match is None:
                return str(node.value)
            env_name = match.group(1)
            env = os.environ[env_name]
            # cast the env var's value
            try:
                config_element = ast.literal_eval(env)
            except Exception:
                config_element = env
            logging.debug(
                f"Replaced environment variable {env_name} with {config_element}"
            )
            return config_element

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

    with open(fname) as f:
        cfg = yaml.load(f.read(), Loader=YamlLoader)

    return cfg
