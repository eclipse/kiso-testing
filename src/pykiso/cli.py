"""
Integration Test Framework
**************************

:module: cli

:synopsis: Entry point to the integration test framework

.. currentmodule:: cli


:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

"""

import logging
import argparse
import click
import json
import pathlib
import time
import yaml
import pprint
import typing

import os
import sys

from . import test_factory_and_execution
from . import __version__
from .types import PathType


def initialize_logging(log_path: PathType, log_level: str) -> logging.Logger:
    """ Initialize the logging

    sets the general log level, output file or STDOUT and the
    logging format.

    :param log_path: path to the logfile
    :param log_level: any of DEBUG, INFO, WARNING, ERROR

    :returns: the Logger
    """

    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    kwargs = {
        "level": levels[log_level],
    }
    if log_path is not None:
        log_path = pathlib.Path(log_path)
        if log_path.is_dir():
            fname = time.strftime("%Y-%m-%d_%H-%M-test.log")
            log_path = log_path / fname
        kwargs["filename"] = log_path

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        **kwargs,
    )
    return logging.getLogger(__name__)


def parse_config(fname: PathType) -> typing.Dict:
    """ Parse YAML config file

    :param fname: path to the config file

    :return: config dict with resolved paths where needed """
    with open(fname) as f:
        cfg = yaml.safe_load(f.read())
    # fix suite-dirs
    base_dir = pathlib.Path(fname).resolve().parent

    def _fix_suite_path(suite):
        if not pathlib.Path(suite["suite_dir"]).is_absolute():
            suite["suite_dir"] = base_dir / suite["suite_dir"]
            logging.debug(
                f'resolved path for suite {suite["test_suite_id"]}: {suite["suite_dir"]}'
            )
        return suite

    def _fix_types_loc(thing):
        loc, _class = thing["type"].rsplit(":", 1)
        if loc.startswith("pykiso.lib"):
            return thing
        path = pathlib.Path(loc)
        if not path.is_absolute():
            thing["type"] = str(base_dir / path) + ":" + _class
            logging.debug(f'resolved path : {thing["type"]}')
        return thing

    cfg["connectors"] = {n: _fix_types_loc(s) for n, s in cfg["connectors"].items()}
    cfg["auxiliaries"] = {n: _fix_types_loc(s) for n, s in cfg["auxiliaries"].items()}
    cfg["test_suite_list"] = [_fix_suite_path(s) for s in cfg["test_suite_list"]]
    return cfg


@click.command()
@click.option(
    "-c",
    "--test-configuration-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
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
    type=click.Choice("DEBUG INFO WARNING ERROR".split(" "), case_sensitive=False,),
    help="set the verbosity of the logging",
)
@click.version_option(__version__)
def main(
    test_configuration_file: PathType,
    log_path: PathType = None,
    log_level: str = "INFO",
):
    """ Embedded Integration Test Framework - CLI Entry Point

    :param test_configuration_file: path to the YAML config file
    :param log_path: path to directory or file to write logs to
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    """
    # Set the logging
    logger = initialize_logging(log_path, log_level)
    # Get YAML configuration
    cfg_dict = parse_config(test_configuration_file)
    # Run tests
    logger.debug("cfg_dict:\n{}".format(pprint.pformat(cfg_dict)))
    test_factory_and_execution.run(cfg_dict)


if __name__ == "__main__":
    main()
