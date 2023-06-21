##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import sys
from pathlib import Path

import pytest

from pykiso import logging_initializer


@pytest.mark.parametrize(
    "path, level, expected_level, expected_path_type, verbose, report_type",
    [
        (None, "INFO", logging.INFO, type(None), False, "junit"),
        ("test/test", "WARNING", logging.WARNING, Path, True, "text"),
        (None, "ERROR", logging.ERROR, type(None), False, None),
    ],
)
def test_initialize_logging(
    mocker, path, level, expected_level, expected_path_type, verbose, report_type
):
    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)
    mkdir_mock = mocker.patch("pathlib.Path.mkdir")
    flush_mock = mocker.patch("logging.StreamHandler.flush", return_value=None)

    logger = logging_initializer.initialize_logging(path, level, verbose, report_type)

    if report_type == "junit":
        flush_mock.assert_called()

    if path is not None:
        mkdir_mock.assert_called()
    else:
        mkdir_mock.assert_not_called()
    if verbose is True:
        assert hasattr(logging, "INTERNAL_INFO")
        assert hasattr(logging, "INTERNAL_WARNING")
        assert hasattr(logging, "INTERNAL_DEBUG")
        assert logging_initializer.log_options.verbose == True
    assert isinstance(logger, logging.Logger)
    assert logger.isEnabledFor(expected_level)
    assert isinstance(logging_initializer.log_options.log_path, expected_path_type)
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


class TestLogger(logging.Logger):
    def __init__(self, name: str, level=0) -> None:
        super().__init__(name, level)
        self.addHandler(logging.StreamHandler())


def test_import_object(mocker):
    import_module_mock = mocker.patch("importlib.import_module", return_value="module")
    get_attr_mock = mocker.patch(
        "pykiso.logging_initializer.getattr", return_value=TestLogger
    )

    object = logging_initializer.import_object("test.path.object")
    no_path_object = logging_initializer.import_object(None)

    assert no_path_object is None
    assert object == TestLogger
    import_module_mock.assert_called_once_with("test.path")
    get_attr_mock.assert_called_once_with("module", "object")


def test_import_object_error(mocker):
    import_module_mock = mocker.patch("importlib.import_module", return_value="module")
    get_attr_mock = mocker.patch(
        "pykiso.logging_initializer.getattr", return_value=logging.Manager
    )
    with pytest.raises(TypeError):
        logging_initializer.import_object("test.path.object")

    import_module_mock.assert_called_once_with("test.path")
    get_attr_mock.assert_called_once_with("module", "object")


def test_add_filter_to_handler():
    TestLogger.__init__ = logging_initializer.add_filter_to_handler(TestLogger.__init__)

    log = TestLogger("test")

    assert isinstance(
        log.handlers[0].filters[0], logging_initializer.InternalLogsFilter
    )


def test_remove_handler_from_logger():
    TestLogger.__init__ = logging_initializer.remove_handler_from_logger(
        TestLogger.__init__
    )

    log = TestLogger("test")

    assert log.handlers == []


@pytest.mark.parametrize(
    "logger_class",
    [
        ("LoggerNewClass(host='test')"),
        ("LoggerNewClass"),
    ],
)
def test_change_logger_class(mocker, logger_class):
    root_save = logging.getLogger()
    set_logger_class_mock = mocker.patch("logging.setLoggerClass")
    save_log = {}
    for name, module in sys.modules.items():
        if getattr(module, "log", None):
            save_log[name] = module.log

    class LoggerNewClass(logging.Logger):
        def __init__(self, name: str, level=0, host="test") -> None:
            super().__init__(name, level)

    import_object_mock = mocker.patch(
        "pykiso.logging_initializer.import_object", return_value=LoggerNewClass
    )
    logging_initializer.change_logger_class("INFO", False, logger_class)
    assert isinstance(logging.root, LoggerNewClass)
    assert isinstance(logging.Logger.manager.root, LoggerNewClass)
    set_logger_class_mock.assert_called_once_with(LoggerNewClass)
    import_object_mock.assert_called_once_with("LoggerNewClass")
    assert isinstance(
        sys.modules["pykiso.test_coordinator.test_case"].log, LoggerNewClass
    )
    logging.root = root_save
    logging.Logger.manager.root = root_save
    for name, module in sys.modules.items():
        if getattr(module, "log", None):
            module.log = save_log[name]
