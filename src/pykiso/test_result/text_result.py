##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Text Test Result with banners
*****************************

:module: text_result

:synopsis: implements a test result that displays the test execution
    wrapped in banners.

.. currentmodule:: text_result
"""

from __future__ import annotations

import logging
import os
import sys
import textwrap
import time
import typing
from contextlib import nullcontext
from shutil import get_terminal_size
from typing import List, Optional, TextIO, Union
from unittest import TextTestResult
from unittest.case import _SubTest

from ..test_coordinator.test_case import BasicTest
from ..test_coordinator.test_suite import BaseTestSuite

if typing.TYPE_CHECKING:
    from pykiso.types import ExcInfoType, PathType

log = logging.getLogger(__name__)


class ResultStream:
    """Class that duplicates sys.stderr to a log file if a file path is provided.

    When passed to a TestRunner or a TestResult, this allows to display the
    information from the test run in the log file.
    """

    def __new__(cls, file: Optional[PathType]):
        """Customize class creation to return an instance of this class
        if a file path is provided, or simply ``sys.stderr`` if no file
        path is provided.

        :param file: the file to write stderr to.
        :return: an instance of this class or ``sys.stderr``.
        """
        # don't bother instanciating and simply return stderr as context manager
        if file is None:
            return nullcontext(sys.stderr)
        # otherwise return a real instance
        return super().__new__(cls)

    def __init__(self, file: Optional[PathType]):
        """Initialize the streams.

        :param file: file where stderr should be written.
        """
        self.stderr = sys.stderr
        self.file: TextIO = open(file, mode="a")
        sys.stderr = self

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, message: str):
        self.stderr.write(message)
        self.file.write(message)

    def flush(self):
        self.stderr.flush()
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        """Close or restore each stream."""
        if self.stderr is not None:
            sys.stderr = self.stderr
            self.stderr = None

        if self.file is not None:
            self.file.close()
            self.file = None


class BannerTestResult(TextTestResult):
    """TextTestResult subclass showing results wrapped in banners (frames)."""

    BANNER_CHAR_WIDTH = 4

    def __init__(self, stream: TextIO, descriptions: bool, verbosity: int):
        """Constructor. Initialize TextTestResult and the banner's width.

        The banner's width is set to the terminal size. In the case
        where this fails the fallback width corresponds to the default
        width of a Jenkins "console".

        :param stream: stream to print the result information
            (default: stderr)
        :param descriptions: unused (required for TextTestResult)
        :param verbosity: unused (required for TextTestResult)
        """
        super().__init__(stream, descriptions, verbosity)
        # to determine whether the test succeeded or failed
        self._error_occurred = False
        # fallback is the default width in Jenkins
        size = get_terminal_size(fallback=(150, 24))
        # avoid border effects due to newlines
        self.width = size.columns - 1
        self.successes: List[Union[BasicTest, BaseTestSuite]] = []

    @property
    def error_occurred(self):
        return self._error_occurred

    def _banner(
        self, text: Union[List, str], width: Optional[int] = None, sym: str = "#"
    ) -> str:
        """Format the provided text within a frame composed of the provided
        symbol.

        Works with multiline strings (either as a string containing
        newlines or split into a list with one entry per line).

        :param text: text to format
        :paran width: width of the banner
        :param sym: symbol used to compose the banner
        :return: the text enclosed in a banner
        """
        width = width or self.width
        line = sym * width
        if isinstance(text, str):
            text = text.split("\n")
        if isinstance(text, list):
            text = "\n".join(
                f"{sym} {line: <{width-self.BANNER_CHAR_WIDTH}} {sym}" for line in text
            )
        banner = f"{line}\n{text}\n{line}\n"
        return banner

    def getDescription(self, test: Union[BasicTest, BaseTestSuite]) -> str:
        """Return the entire test method docstring.

        :param test: running testcase
        :return: the wrapped docstring
        """
        doc = ""
        if getattr(test, "_testMethodDoc", None) is not None:
            for line in test._testMethodDoc.splitlines():
                doc += "\n" + textwrap.fill(
                    line.strip(), width=self.width - self.BANNER_CHAR_WIDTH
                )
        return doc

    def startTest(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Print a banner containing the test information and the test
        method docstring when starting a test case.

        :param test: testcase that is about to be run
        """
        super().startTest(test)
        self._error_occurred = False
        # gather test module, test class, test method and test description
        module_name = test.__module__
        test_name = str(test)
        addendum = ""
        doc = self.getDescription(test).rstrip()
        # verify if the test case is skipped
        is_skipped = False
        if getattr(test, "__unittest_skip__", False):
            # in case of an entirely skipped test class only the top
            # banner is printed
            top_str = "SKIPPED TEST: "
            addendum += f"\nReason: {test.__unittest_skip_why__}"
            is_skipped = True
        else:
            top_str = "RUNNING TEST: "
        if len(module_name + test_name) < self.width - len(top_str):
            test_name = f"{module_name}.{test_name}"
        else:
            addendum += f"\nmodule: {module_name}"
        # create and print test start banner
        top_str += f"{test_name}{addendum}{doc}"
        top_banner = self._banner(top_str)
        if is_skipped:
            top_banner += "\n"
        self.stream.write(top_banner)
        self.stream.flush()
        # start monitoring test duration
        test.start_time = time.time()

    def stopTest(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Print a banner containing the test information and its result.

        :param test: terminated testcase
        """
        if getattr(test, "__unittest_skip__", False):
            return super().stopTest(test)
        test.stop_time = time.time()
        test.elapsed_time = test.stop_time - test.start_time
        result = "FAILED" if self.error_occurred else "PASSED"
        bot_str = f"END OF TEST: {test}"
        result_str = f"  ->  {result} in {test.elapsed_time:.3f}s"
        if len(bot_str + result_str) < self.width - self.BANNER_CHAR_WIDTH:
            bot_str += result_str
        else:
            bot_str += "\n" + result_str
        bot_banner = self._banner(bot_str) + "\n"
        self.stream.write(bot_banner)
        self.stream.flush()
        super().stopTest(test)

    def addFailure(
        self, test: Union[BasicTest, BaseTestSuite], err: ExcInfoType
    ) -> None:
        """Set the error flag when a failure occurs in order to get the
        individual test case result.

        :param test: testcase which failure will be reported
        :param err: tuple returned by sys.exc_info
        """
        super().addFailure(test, err)
        self._error_occurred = True

    def addSuccess(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Add a testcase to the list of succeeded test cases.

        :param test: running testcase that succeeded
        """
        self.successes.append(test)

    def addError(self, test: Union[BasicTest, BaseTestSuite], err: ExcInfoType) -> None:
        """Set the error flag when an error occurs in order to get the
        individual test case result.

        :param test: running testcase that errored out
        :param err: tuple returned by sys.exc_info
        """
        super().addError(test, err)
        self._error_occurred = True

    def addSubTest(
        self,
        test: Union[BasicTest, BaseTestSuite],
        subtest: _SubTest,
        err: ExcInfoType,
    ) -> None:
        """Set the error flag when an error occurs in a subtest.

        :param test: running testcase
        :param subtest: subtest runned
        :param err: tuple returned by sys.exc_info
        """
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._error_occurred = True

    def printErrorList(self, flavour: str, errors: List[tuple]):
        """Print all errors at the end of the whole tests execution.

        Overwrites the unittest method to have a nicer output.

        :param flavour: failure reason
        :param errors: list of failed tests with their error message
        """
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s" % test)
            self.stream.writeln("%s" % self.getDescription(test))
            self.stream.writeln("%s: %s" % (flavour, err))
