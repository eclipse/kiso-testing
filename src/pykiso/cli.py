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
import itertools
import logging
import pprint
import sys
import time
from pathlib import Path
from typing import NamedTuple, Optional, Tuple

import click

from . import __version__
from .config_parser import parse_config
from .global_config import Grabber
from .test_coordinator import test_execution
from .test_setup.config_registry import ConfigRegistry
from .types import PathType

LogOptions = collections.namedtuple("LogOptions", "log_path log_level report_type")

# use to store the selected logging options
log_options: Optional[NamedTuple] = None


def initialize_logging(
    log_path: PathType, log_level: str, report_type: str = None
) -> logging.Logger:
    """Initialize the logging.

    Sets the general log level, output file or STDOUT and the
    logging format.

    :param log_path: path to the logfile
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :param report_type: expected report type (junit, text,...)

    :returns: configured Logger
    """
    root_logger = logging.getLogger()
    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(module)s:%(lineno)d: %(message)s"
    )
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    # update logging options
    global log_options
    log_options = LogOptions(log_path, log_level, report_type)

    # if log_path is given create use a logging file handler
    if log_path is not None:
        log_path = Path(log_path)
        if log_path.is_dir():
            fname = time.strftime("%Y-%m-%d_%H-%M-test.log")
            log_path = log_path / fname
        file_handler = logging.FileHandler(log_path, "a+")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(levels[log_level])
        root_logger.addHandler(file_handler)
    # if log_path is not given and report type is not junit just
    # instanciate a logging StreamHandler
    if log_path is None and report_type != "junit":
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        stream_handler.setLevel(levels[log_level])
        root_logger.addHandler(stream_handler)
    # if report_type is junit use sys.stdout as stream
    if report_type == "junit":
        # flush all StreamHandler
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.flush()
        # but keep FileHandler
        root_logger.handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_format)
        stream_handler.setLevel(levels[log_level])
        root_logger.addHandler(stream_handler)

    root_logger.setLevel(levels[log_level])

    return logging.getLogger(__name__)


def get_logging_options() -> LogOptions:
    """Simply return the previous logging options.

    :return: logging options log path, log level and report type
    """
    return log_options


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-c",
    "--test-configuration-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    multiple=True,
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
    "--variant",
    multiple=True,
    type=str,
    default=None,
    help="allow the user to execute a subset of tests based on variants",
)
@click.option(
    "--branch-level",
    multiple=True,
    type=str,
    default=None,
    help="allow the user to execute a subset of tests based on branch levels",
)
@click.option(
    "--failfast",
    is_flag=True,
    help="stop the test run on the first error or failure",
)
@click.argument("pattern", required=False)
@click.version_option(__version__)
@Grabber.grab_cli_config
def main(
    test_configuration_file: Tuple[PathType],
    log_path: PathType = None,
    log_level: str = "INFO",
    report_type: str = "text",
    variant: Optional[tuple] = None,
    branch_level: Optional[tuple] = None,
    pattern: Optional[str] = None,
    failfast: bool = False,
):
    """Embedded Integration Test Framework - CLI Entry Point.

    PATTERN: overwrite the test filter pattern from the YAML file (optional)

    \f
    :param test_configuration_file: path to the YAML config file
    :param log_path: path to directory or file to write logs to
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :param report_type: if "test", the standard report, if "junit", a junit report is generated
    :param variant: allow the user to execute a subset of tests based on variants
    :param branch_level: allow the user to execute a subset of tests based on branch levels
    :param pattern: overwrite the pattern from the YAML file for easier testdevelopment
    :param failfast: stop the test run on the first error or failure
    """

    if log_path and Path(log_path).is_file():
        Path(log_path).unlink()

    for config_file in test_configuration_file:
        # Set the logging
        logger = initialize_logging(log_path, log_level, report_type)
        # Get YAML configuration
        cfg_dict = parse_config(config_file)
        # Run tests
        logger.debug("cfg_dict:\n{}".format(pprint.pformat(cfg_dict)))

        ConfigRegistry.register_aux_con(cfg_dict)

        exit_code = test_execution.execute(
            cfg_dict, report_type, variant, branch_level, pattern, failfast
        )
        ConfigRegistry.delete_aux_con()
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                logging.getLogger().removeHandler(handler)

    sys.exit(exit_code)
