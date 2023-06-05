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
from typing import TYPE_CHECKING

import pytest

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
    pytest_logger: LoggingPlugin = session.config.pluginmanager.get_plugin(
        "logging-plugin"
    )
    if pytest_logger.log_cli_level is None:
        pytest_logger.log_cli_level = logging.INFO
    # run pykiso's logging initialization
    initialize_logging(
        log_path=None,
        log_level=logging.getLevelName(pytest_logger.log_cli_level),
        report_type="text",
        # display internal logs at least -vv is provided
        verbose=(session.config.getoption("verbose") > 1),
    )
    root_logger = logging.getLogger()

    # get all handlers that were configured by pykiso and remove them
    stream_handlers = [
        hdlr for hdlr in root_logger.handlers if isinstance(hdlr, logging.StreamHandler)
    ]
    file_handlers = [
        hdlr for hdlr in root_logger.handlers if isinstance(hdlr, logging.FileHandler)
    ]
    for hdlr in stream_handlers + file_handlers:
        root_logger.removeHandler(hdlr)

    root_logger.addHandler(pytest_logger.log_cli_handler)
    root_logger.addHandler(pytest_logger.log_file_handler)
