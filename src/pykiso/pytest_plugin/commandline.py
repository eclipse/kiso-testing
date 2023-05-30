##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Pytest command line extension
*****************************

:module: commandline

:synopsis: add pykiso-related options and ini values to pytest.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import export

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.main import PytestPluginManager


@export
def pytest_cmdline_main(config: Config):
    """Extract and reformat the CLI-provided tags as a dictionary.

    :param config: the pytest config instance.
    """

    def format_tags(unknown_args: list[str]) -> dict[str, list[str]]:
        formatted_args = dict()
        for arg in unknown_args:
            key, value = arg.split("=")
            key = key.replace("--", "", 1)
            key = key.replace("-", "_")
            formatted_args[key] = value.split(",")
        return formatted_args

    user_tags = config.getoption("tags", default=None)
    config.option.tags = format_tags(user_tags) if user_tags is not None else None


@export
def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager) -> None:
    """Add the 'tags' option to pytest's command line interface
    and the 'auxiliary_scope' ini value.

    :param parser: the command line parser.
    :param pluginmanager: not used.
    """
    group = parser.getgroup("pykiso")
    group.addoption(
        "--tags",
        nargs="+",
        dest="tags",
        help="Additional test tags to select tests to run depending on the tag value, "
        "e.g. '--tags variant=var1,var2 level=daily'",
    )
    parser.addini(
        "auxiliary_scope",
        default="session",
        type="string",
        help="Change this value to any of 'session', 'module', 'class', 'function' to change the "
        "scope for all auxiliaries. "
        "Note that if you define a scope of e.g. 'function', you won't be able to request a higher "
        "scope for an auxiliary by overriding the associated fixture.",
    )
