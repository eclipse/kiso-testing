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

:module: test_result

:synopsis: implement BannerTestResult to show detailed test execution
wrapped in banners.

.. currentmodule:: test_result
"""

import textwrap
import time
from shutil import get_terminal_size
from typing import List, Optional, TextIO, Union
from unittest import TestCase, TestResult, TextTestResult


class BannerTestResult(TextTestResult):
    """TextTestResult subclass showing results wrapped in banners."""

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
        # disable TextTestResult printing
        self.dots = False
        self.verbosity = False
        self._error_occurred = False
        # fallback is the default width in Jenkins
        size = get_terminal_size(fallback=(150, 24))
        # avoid border effects due to newlines
        self.width = size.columns - 1
        self.successes: List[TestCase] = []

    def _banner(
        self, text: Union[List, str], width: Optional[int] = None, sym: str = "#"
    ) -> str:
        """Format text as a banner.

        Works with multiline strings (either as a string containing
        newlines or split into a list with one entry per line).

        :param text: text to format
        :paran width: width of the banner
        :param sym: symbol used to compose the banner

        :return: the text enclosed in a banner
        """
        width = width or self.width
        bar = sym * width
        if isinstance(text, str):
            text = text.split("\n")
        if isinstance(text, list):
            text = "\n".join(f"{sym} {line: <{width-4}} {sym}" for line in text)
        banner = f"{bar}\n{text}\n{bar}\n"
        return banner

    def getDescription(self, test: TestCase) -> str:
        """Return the entire test method docstring.

        :param test: running testcase

        :return: the wrapped docstring
        """
        doc = ""
        if getattr(test, "_testMethodDoc", None) is not None:
            doc = "\n"
            for line in test._testMethodDoc.splitlines():
                doc += "\n" + textwrap.fill(line.strip(), width=100)
        else:
            doc = ""
        return doc

    def startTest(self, test: TestCase) -> None:
        """Print a banner containing the test information and the test
        method docstring when starting a test case.

        :param test: running testcase
        """
        TestResult.startTest(self, test)
        self._error_occurred = False
        top_str = "RUNNING TEST: "
        module_name = test.__module__
        test_name = str(test)
        addendum = ""
        doc = self.getDescription(test)
        if len(module_name + test_name) < self.width - len(top_str):
            test_name = f"{module_name}.{test_name}"
        else:
            addendum += f"\nmodule: {module_name}"
        top_str += f"{test_name}{addendum}{doc}"
        top_banner = self._banner(top_str)
        self.stream.write(top_banner)
        self.stream.flush()
        test.start_time = time.time()

    def stopTest(self, test: TestCase) -> None:
        """Print a banner containing the test information and its result.

        :param test: running testcase
        """
        test.stop_time = time.time()
        test.elapsed_time = test.stop_time - test.start_time
        result = "Failed" if self._error_occurred else "Passed"
        bot_str = f"END OF TEST: {test}"
        result_str = f"  ->  {result}"
        if len(bot_str + result_str) < self.width:
            bot_str += result_str
        else:
            bot_str += "\n" + result_str
        bot_banner = self._banner(bot_str) + "\n"
        self.stream.write(bot_banner)
        self.stream.flush()
        TestResult.stopTest(self, test)

    def addFailure(self, test: TestCase, err: tuple) -> None:
        """Set the error flag when a failure occurs in order to get the
        individual test case result.

        :param test: running testcase
        :param err: tuple returned by sys.exc_info
        """
        TestResult.addFailure(self, test, err)
        self._error_occurred = True

    def addSuccess(self, test: TestCase) -> None:
        """Add a testcase to the list of succeeded test cases.

        :param test: running testcase
        """
        self.successes.append(test)

    def addError(self, test: TestCase, err: tuple) -> None:
        """Set the error flag when an error occurs in order to get the
        individual test case result.

        :param test: running testcase
        :param err: tuple returned by sys.exc_info
        """
        TestResult.addError(self, test, err)
        self._error_occurred = True

    def printErrorList(self, flavour: str, errors: List[tuple]):
        """Print all errors at the end of the whole tests execution
        Overwrite the unit-test function

        :param flavour: failure reason
        :param errors: list of failed tests with their error message
        """
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s" % test)
            self.stream.writeln("%s" % self.getDescription(test))
            self.stream.writeln("%s: %s" % (flavour, err))
