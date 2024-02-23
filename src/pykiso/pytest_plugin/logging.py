##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Logging configuration
*********************

:module: logging

:synopsis: initialize the pykiso loggers and patch then onto pytest's loggers
    in order to control CLI and file logging with pytest's built-in options.

"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import pytest
from _pytest.logging import ColoredLevelFormatter

from pykiso.logging_initializer import initialize_logging

from .utils import *

if TYPE_CHECKING:
    from _pytest.logging import LoggingPlugin
    from _pytest.main import Session


@export
@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session: Session):
    """Initialize pykiso logging and patch the resulting loggers onto
    pytest's logger at session start.

    Try to run this hook implementation at last to ensure that logging
    is already preconfigured by pytest.

    :param session: the current test session.
    """
    # get pytest's logger as plugin
    pytest_logger: LoggingPlugin = session.config.pluginmanager.get_plugin("logging-plugin")
    if pytest_logger.log_cli_level is None:
        pytest_logger.log_cli_level = logging.INFO

    # run pykiso's logging initialization
    if pytest_logger.log_file_handler.baseFilename == os.devnull:
        log_file_path = None
    else:
        log_file_path = pytest_logger.log_file_handler.baseFilename

    initialize_logging(
        log_path=log_file_path,
        log_level=logging.getLevelName(pytest_logger.log_cli_level),
        report_type="text",
        # display internal logs at least -vv is provided
        verbose=(session.config.getoption("verbose") > 1),
    )
    root_logger = logging.getLogger()
    # get all handlers that were configured by pykiso to retrieve their level
    stream_handler = next(
        (hdlr for hdlr in root_logger.handlers if type(hdlr) == logging.StreamHandler),
        None,
    )
    file_handler = next(
        (hdlr for hdlr in root_logger.handlers if type(hdlr) == logging.FileHandler),
        None,
    )
    if pytest_logger.log_cli_handler.level != logging.NOTSET and stream_handler is not None:
        pytest_logger.log_cli_level = stream_handler.level
        pytest_logger.log_cli_handler.level = stream_handler.level
        if isinstance(pytest_logger.log_cli_handler.formatter, ColoredLevelFormatter):
            pytest_logger.log_cli_handler.formatter.add_color_level(logging.INTERNAL_WARNING, "yellow", "light")
            pytest_logger.log_cli_handler.formatter.add_color_level(logging.INTERNAL_INFO, "green", "light")
            pytest_logger.log_cli_handler.formatter.add_color_level(logging.INTERNAL_DEBUG, "purple", "light")

    if pytest_logger.log_file_handler.level != logging.NOTSET and file_handler is not None:
        pytest_logger.log_file_handler.level = file_handler.level
        pytest_logger.log_file_level = file_handler.level

    root_logger.handlers.clear()
    pytest_logger.log_level = root_logger.level

    root_logger.addHandler(pytest_logger.log_cli_handler)
    root_logger.addHandler(pytest_logger.log_file_handler)
