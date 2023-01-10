##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Integration Test Framework
**************************

:module: cli

:synopsis: Entry point to the integration test framework.

.. currentmodule:: cli

"""
import collections
import logging
import pprint
import sys
import time
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

import click

from pykiso.test_coordinator.test_execution import ExitCode

from . import __version__
from .config_parser import parse_config
from .global_config import Grabber
from .logging_initializer import initialize_logging
from .test_coordinator import test_execution
from .test_setup.config_registry import ConfigRegistry
from .types import PathType


def eval_user_tags(click_context: click.Context) -> Dict[str, List[str]]:
    """Evaluate commandline args for user tags and raise exceptions for invalid
    arguments.

    :param click_context: click context
    :raises click.NoSuchOption: if key doesnt start with "--" or has an invalid
      character like "_"
    :raises click.BadOptionUsage: no value specfied for user tag
    :return: user tags with values
    """
    user_tags = {}
    user_args = click_context.args.copy()
    if not user_args:
        return user_tags
    while user_args:
        try:
            key = user_args.pop(0)
            if not key.startswith("--") or "_" in key:
                correct_key = (
                    f'{"" if key.startswith("--") else "--" }{key.replace("_","-")}'
                )
                raise click.NoSuchOption(option_name=key, possibilities=[correct_key])

            value = user_args.pop(0)
            user_tags[key[2:]] = value.split(",")
        except IndexError:
            raise click.BadOptionUsage(
                option_name=key,
                message=f"No value specified for tag {key}",
                ctx=click_context,
            )
    return user_tags


def check_file_extension(
    click_context: click.Context, param: click.Parameter, paths: Tuple[str]
) -> Tuple[str]:
    """Check the path strings of all given test configuration files for yaml file
    extension and raise an exception if the check fails

    :click_context: click context (click callback requirement)
    :param: click parameter (click callback requirement)
    :paths: the paths of the files to check
    :raises click.BadParameter: if one of the files does not have .yaml or .yml
        as extension
    :return: the checked paths as they were passed
    """
    for path in paths:
        if not path.endswith((".yaml", ".yml")):
            raise click.BadParameter(
                f"Configuration needs to be a .yaml file, but {path} was given"
            )
    return paths


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.option(
    "-c",
    "--test-configuration-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    multiple=True,
    callback=check_file_extension,
    help="path to the test configuration file (in YAML format)",
)
@click.option(
    "-l",
    "--log-path",
    required=False,
    default=None,
    type=click.Path(writable=True),
    help="path to log-file or folder. If not set will log to STDOUT",
)
@click.option(
    "--log-level",
    required=False,
    default="INFO",
    type=click.Choice(
        "DEBUG INFO WARNING ERROR".split(" "),
        case_sensitive=False,
    ),
    help="set the verbosity of the logging",
)
@click.option(
    "--junit",
    "report_type",
    flag_value="junit",
    required=False,
    help="enables the generation of a junit report",
)
@click.option(
    "--text",
    "report_type",
    flag_value="text",
    required=False,
    default=True,
    help="default, test results are only displayed in the console",
)
@click.option(
    "--step-report",
    required=False,
    default=None,
    type=click.Path(writable=True),
    help="generate the step report at the specified path",
)
@click.option(
    "--failfast",
    is_flag=True,
    help="stop the test run on the first error or failure",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    required=False,
    help="activate the internal framework logs",
)
@click.option(
    "-p",
    "--pattern",
    type=click.STRING,
    required=False,
    help="test filter pattern, e.g. 'test_suite_1.py' or 'test_*.py'. Or even more granularly 'test_suite_1.py::TestClass::test_name'",
)
@click.version_option(__version__)
@Grabber.grab_cli_config
@click.pass_context
def main(
    click_context: click.Context,
    test_configuration_file: Tuple[PathType],
    log_path: PathType = None,
    log_level: str = "INFO",
    report_type: str = "text",
    step_report: Optional[PathType] = None,
    pattern: Optional[str] = None,
    failfast: bool = False,
    verbose: bool = False,
):
    """Embedded Integration Test Framework - CLI Entry Point.

    TAG Filters: any additional option to be passed to the test as tag through
    the pykiso call. Multiple values must be separated with a comma.

    For example: pykiso -c your_config.yaml --branch-level dev,master --variant delta

    \f
    :param click_context: click context
    :param test_configuration_file: path to the YAML config file
    :param log_path: path to an existing directory or file to write logs to
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :param report_type: if "test", the standard report, if "junit", a junit report is generated
    :param variant: allow the user to execute a subset of tests based on variants
    :param branch_level: allow the user to execute a subset of tests based on branch levels
    :param step_report: file path for the step report or None
    :param pattern: overwrite the pattern from the YAML file for easier test development
    :param failfast: stop the test run on the first error or failure
    :param verbose: activate logging for the whole framework
    """

    for config_file in test_configuration_file:
        # Set the logging
        logger = initialize_logging(log_path, log_level, verbose, report_type)
        # Get YAML configuration
        cfg_dict = parse_config(config_file)
        # Run tests
        logger.debug("cfg_dict:\n{}".format(pprint.pformat(cfg_dict)))

        ConfigRegistry.register_aux_con(cfg_dict)

        user_tags = eval_user_tags(click_context)

        exit_code = test_execution.execute(
            cfg_dict, report_type, user_tags, step_report, pattern, failfast
        )
        ConfigRegistry.delete_aux_con()
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                logging.getLogger().removeHandler(handler)

    sys.exit(exit_code)
