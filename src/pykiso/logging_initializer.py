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
import logging
import sys
import time
from pathlib import Path
from typing import List, NamedTuple, Optional

from .test_setup.dynamic_loader import PACKAGE
from .types import PathType


class LogOptions(NamedTuple):
    """
    Namedtuple containing the available options for logging configuration.
    """

    log_path: PathType
    log_level: str
    report_type: str
    verbose: bool


# used to store the selected logging options
log_options: Optional[LogOptions] = None

# used to store the loggers that shouldn't be silenced
active_loggers = set()


def get_logging_options() -> LogOptions:
    """Simply return the previous logging options.

    :return: logging options log path, log level and report type
    """
    return log_options


def add_internal_log_levels() -> None:
    """Create pykiso's internal log levels if not already done."""
    if not hasattr(logging, "INTERNAL_WARNING"):
        add_logging_level("INTERNAL_WARNING", logging.WARNING + 1)
        add_logging_level("INTERNAL_INFO", logging.INFO + 1)
        add_logging_level("INTERNAL_DEBUG", logging.DEBUG + 1)


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
    add_internal_log_levels()

    # update logging options
    global log_options
    log_options = LogOptions(log_path, log_level, report_type, verbose)

    class InternalLogsFilter(logging.Filter):
        def filter(self, record):
            """Filters internal log levels

            :param record: event being logged

            :return: False if internal logging, True otherwise
            """
            return record.levelno not in (
                logging.INTERNAL_WARNING,
                logging.INTERNAL_INFO,
                logging.INTERNAL_DEBUG,
            )

    # if log_path is given create a file handler
    if log_path is not None:
        log_path = Path(log_path)
        if log_path.is_dir():
            fname = time.strftime("%Y-%m-%d_%H-%M-test.log")
            log_path = log_path / fname
        file_handler = logging.FileHandler(log_path, "a+")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(levels[log_level])
        root_logger.addHandler(file_handler)

    # if report_type is junit use sys.stdout as stream
    if report_type == "junit":
        stream = sys.stdout
        # flush all StreamHandlers
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.flush()
        # and remove them from the handlers (keep FileHandlers only)
        root_logger.handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
    # report type is not junit just instanciate a StreamHandler that prints to stderr
    else:
        stream = sys.stderr

    # for all report types add a StreamHandler
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setFormatter(log_format)
    stream_handler.setLevel(levels[log_level])
    if not verbose:
        # filter internal log levels
        stream_handler.addFilter(InternalLogsFilter())
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
    >>> add_logging_level('KISO', logging.DEBUG - 5)
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
    global active_loggers
    if loggers is None:
        loggers = list()
    # keyword 'all' should keep all loggers to the configured level
    if "all" in loggers:
        logging.internal_warning(
            "All loggers are activated, this could lead to performance issues."
        )
        active_loggers |= set(logging.root.manager.loggerDict.keys())
        return
    # keep package and auxiliary loggers, store all the others to deactivate them
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

    # store previous loggers to keep active (union of previous and current loggers)
    active_loggers |= set(loggers)

    # set the loggers that are not part of active_loggers to level WARNING
    loggers_to_deactivate = set(relevant_loggers) - set(active_loggers)
    for logger_name in loggers_to_deactivate:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
