##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import logging
import os
from pathlib import Path
from tabnanny import verbose

import pytest

from pykiso import logging_initializer


@pytest.mark.parametrize(
    "path, level, expected_level, verbose, report_type",
    [
        (None, "INFO", logging.INFO, False, "junit"),
        (os.getcwd(), "WARNING", logging.WARNING, True, "text"),
        (None, "ERROR", logging.ERROR, False, None),
    ],
)
def test_initialize_logging(mocker, path, level, expected_level, verbose, report_type):

    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)
    flush_mock = mocker.patch("logging.StreamHandler.flush", return_value=None)

    if path:
        path = Path(path)

    logger = logging_initializer.initialize_logging(path, level, verbose, report_type)

    if report_type == "junit":
        flush_mock.assert_called()
    if verbose is True:
        assert hasattr(logging, "INTERNAL_INFO")
        assert hasattr(logging, "INTERNAL_WARNING")
        assert hasattr(logging, "INTERNAL_DEBUG")
        assert logging_initializer.log_options.verbose == True
    assert isinstance(logger, logging.Logger)
    assert logger.isEnabledFor(expected_level)
    assert logging_initializer.log_options.log_path == path
    assert logging_initializer.log_options.log_level == level
    assert logging_initializer.log_options.report_type == report_type


def test_get_logging_options():

    logging_initializer.log_options = logging_initializer.LogOptions(
        None, "ERROR", None, False
    )

    options = logging_initializer.get_logging_options()

    assert options is not None
    assert options.log_level == "ERROR"
    assert options.report_type is None


def test_deactivate_all_loggers(caplog):

    with caplog.at_level(logging.WARNING):
        logging_initializer.initialize_loggers(["all"])

    assert "All loggers are activated" in caplog.text
