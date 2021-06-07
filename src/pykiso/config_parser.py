##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
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

import io
import logging
import os
import re
import typing
from pathlib import Path

import yaml

from .types import PathType


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
            self._root = Path(fname).parent
            super().__init__(stream)

        def include(self, node: yaml.nodes.ScalarNode) -> dict:
            """Return the content of an yaml file identify by !include
            tag.

            :param node: ScalarNode currently in use

            :return: yaml file content
            """
            filename = self._root / Path(node.value).resolve()
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
        """Search for an environment variable and replace it with the associated value.

        Additionally, cast the value if it matches an integer.

        :param config_element: config sub-dict value

        :return: config sub-dict value with replaced environment variable if needed
        """
        # Check for regular expression "ENV{word}"
        match = re.compile(r"ENV{(\w+)}").findall(str(config_element))
        if match:
            # Parse detected environment variable
            match = str(match[0])
            env = os.environ[match]
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
                f"Replaced environment variable {match} with {config_element}"
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

    return cfg
