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

:module: logging

:synopsis: Handles initialization of the loggers and cutom logging levels.

.. currentmodule:: logging

"""
import collections
import logging
import sys
import time
from pathlib import Path
from typing import List, NamedTuple, Optional

from .test_setup.dynamic_loader import PACKAGE
from .types import PathType

LogOptions = collections.namedtuple("LogOptions", "log_path log_level report_type")
# use to store the selected logging options
log_options: Optional[NamedTuple] = None


def get_logging_options() -> LogOptions:
    """Simply return the previous logging options.

    :return: logging options log path, log level and report type
    """
    return log_options


def initialize_logging(
    log_path: PathType,
    log_level: str,
    verbose: bool,
    report_type: str = None,
) -> logging.Logger:
    """Initialize the logging.

    Sets the general log level, output file or STDOUT and the
    logging format.

    :param log_path: path to the logfile
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :param verbose: activate internal kiso logging if True
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
    # add internal kiso log levels
    if verbose:
        add_logging_level("INTERNAL_WARNING", logging.WARNING + 1)
        add_logging_level("INTERNAL_INFO", logging.INFO + 1)
        add_logging_level("INTERNAL_DEBUG", logging.DEBUG + 1)
    else:
        # As level value is < than DEBUG value (10), internal kiso logs will be ignored
        add_logging_level("INTERNAL_WARNING", 1)
        add_logging_level("INTERNAL_INFO", 1)
        add_logging_level("INTERNAL_DEBUG", 1)

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


def add_logging_level(level_name: str, level_num: int):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `level_name` becomes an attribute of the `logging` module with the value
    `level_num`.
    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present
    Inspired by: https://stackoverflow.com/a/35804945

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("KISO")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.kiso('so did this')
    >>> logging.KISO
    5

    :param level_name: name of the new level
    :param level_num: value of the new level
    """
    method_name = level_name.lower()

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    if not hasattr(logging, level_name):
        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging.getLoggerClass(), method_name, log_for_level)
        setattr(logging, method_name, log_to_root)


def initialize_loggers(loggers: Optional[List[str]]) -> None:
    """Deactivate all external loggers except the specified ones.

    :param loggers: list of logger names to keep activated
    """
    if loggers is None:
        loggers = list()
    # keyword 'all' should keep all loggers to the configured level
    if "all" in loggers:
        logging.internal_warning(
            "All loggers are activated, this could lead to performance issues."
        )
        return
    # keep package and auxiliary loggers
    relevant_loggers = {
        name: logger
        for name, logger in logging.root.manager.loggerDict.items()
        if not (name.startswith(PACKAGE) or name.endswith("auxiliary"))
        and not isinstance(logger, logging.PlaceHolder)
    }
    # keep child loggers
    childs = [
        logger
        for logger in relevant_loggers.keys()
        for parent in loggers
        if (logger.startswith(parent) or parent.startswith(logger))
    ]
    loggers += childs
    # keep original level for specified loggers
    loggers_to_deactivate = set(relevant_loggers) - set(loggers)
    for logger_name in loggers_to_deactivate:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
