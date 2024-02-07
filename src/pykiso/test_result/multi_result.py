##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Multi test result
*****************

:module: multi_result

:synopsis: a test result proxy that allows to use a ``TestRunner`` with multiple
    `` TestResult`` subclasses

.. currentmodule:: multi_result
"""
from __future__ import annotations

from inspect import signature
from typing import Any, List, Optional, TextIO, Union
from unittest import TestResult
from unittest.case import _SubTest

from pykiso.types import ExcInfoType

from ..test_coordinator.test_case import BasicTest
from ..test_coordinator.test_suite import BaseTestSuite
from .text_result import BannerTestResult
from .xml_result import XmlTestResult


class MultiTestResult:
    """Class that can take multiple test result classes and ran the
    test for all the classes.
    """

    def __init__(self, *result_classes: TestResult):
        """Initialize parameter

        :param result_classes: test result classes
        """
        self.result_classes = result_classes

    def __call__(self, *args, **kwargs) -> MultiTestResult:
        """Initialize the result classes with the parameters passed in arguments."""
        self.result_classes = [
            result(*self._get_arguments_result_class(result, *args, **kwargs)) for result in self.result_classes
        ]
        return self

    def _get_arguments_result_class(self, result_class, *args, **kwargs) -> List[Any]:
        """Function to get the argument for the result class initialisation.

        :param result_class: test result class
        :return: list of arguments to initialise the class
        """
        list_arguments = []
        args = list(args)
        sign_class = signature(result_class)
        for name in sign_class.parameters.keys():
            arg = kwargs.get(name) or (args.pop(0) if args else sign_class.parameters[name].default)
            list_arguments.append(arg)

        return list_arguments

    def __getattr__(self, name: str) -> Any:
        """Function implemented to get the attributes such as error, failures,
            successes,expectedFailures.

        :param name: name of the attribute
        """
        return getattr(self.result_classes[0], name)

    def __setattr__(self, name: str, value: Any) -> Any:
        """Function implemented to set the attributes such as failfast
            of all of the result classes

        :param name: name of the attribute
        """
        super().__setattr__(name, value)
        # condition to avoid infinite loop with the __getattr__
        if name != "result_classes":
            for result in self.result_classes:
                setattr(result, name, value)

    @property
    def error_occurred(self) -> Optional[bool]:
        """Return if an error occurred for a BannerTestResult"""
        for result in self.result_classes:
            if hasattr(result, "error_occurred"):
                return result.error_occurred

    def startTest(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Call the startTest function for all result classes.

        :param test: running testcase
        """
        for result in self.result_classes:
            result.startTest(test)

    def startTestRun(self) -> None:
        """Call the startTestRun function for all result classes."""
        for result in self.result_classes:
            result.startTestRun()

    def stopTestRun(self) -> None:
        """Call the stopTestRun function for all result classes."""
        for result in self.result_classes:
            result.stopTestRun()

    def stop(self) -> None:
        """Call the stop function for all result classes."""
        for result in self.result_classes:
            result.stop()

    def stopTest(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Call the stopTest function for all result classes.

        :param test: running testcase
        """
        for result in self.result_classes:
            result.stopTest(test)

    def addSuccess(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Call the addSuccess function for all result classes.

        :param test: running testcase
        """
        for result in self.result_classes:
            result.addSuccess(test)

    def addSkip(self, test: Union[BasicTest, BaseTestSuite], reason: str) -> None:
        """Call the addSkip function for all result classes.

        :param test: running testcase
        :param reason: reason to skip the test
        """
        for result in self.result_classes:
            result.addSkip(test, reason)

    def addUnexpectedSuccess(self, test: Union[BasicTest, BaseTestSuite]) -> None:
        """Call the addUnexpectedSuccess function for all result classes.

        :param test: running testcase
        """
        for result in self.result_classes:
            result.addUnexpectedSuccess(test)

    def addExpectedFailure(
        self,
        test: Union[BasicTest, BaseTestSuite],
        err: ExcInfoType,
    ) -> None:
        """Call the addExpectedFailure function for all result classes.

        :param test: running testcase
        :param err: tuple returned by sys.exc_info
        """
        for result in self.result_classes:
            result.addExpectedFailure(test, err)

    def addSubTest(
        self,
        test: Union[BasicTest, BaseTestSuite],
        subtest: _SubTest,
        err: ExcInfoType,
    ) -> None:
        """Call the addSubTest function for all result classes.

        :param test: running testcase
        :param subtest: subtest run
        :param err: tuple returned by sys.exc_info
        """
        for result in self.result_classes:
            result.addSubTest(test, subtest, err)

    def addError(
        self,
        test: Union[BasicTest, BaseTestSuite],
        err: ExcInfoType,
    ) -> None:
        """Call the addError function for all result classes.

        :param test: running testcase
        :param err: tuple returned by sys.exc_info
        """
        for result in self.result_classes:
            result.addError(test, err)

    def addFailure(
        self,
        test: Union[BasicTest, BaseTestSuite],
        err: ExcInfoType,
    ) -> None:
        """Call the addFailure function for all result classes.

        :param test: running testcase
        :param err: tuple returned by sys.exc_info
        """
        for result in self.result_classes:
            result.addFailure(test, err)

    def printErrorList(self, flavour: str, errors: List[tuple]) -> None:
        """Call printErrorList function once, it will first try to call the
        function for a BannerTestResult first but if none are defined it will
        call the function of the first result class.

        :param flavour: failure reason
        :param errors: list of failed tests with their error message
        """
        for result in self.result_classes:
            if isinstance(result, BannerTestResult):
                return result.printErrorList(flavour, errors)
        return self.result_classes[0].printErrorList(flavour, errors)

    def printErrors(self) -> None:
        """Call printErrors function once, it will first try to call the function
        for a BannerTestResult first but if none are defined it will call the
        function of the first result class.
        """
        for result in self.result_classes:
            if isinstance(result, BannerTestResult):
                return result.printErrors()
        return self.result_classes[0].printErrors()

    def getDescription(self, test: Union[BasicTest, BaseTestSuite]) -> str:
        """Call getDescription function once, it will first try to call the
        function for a BannerTestResult first but if none are defined it will
        call the function of the first result class available.

        :param test: running testcase
        """
        for result in self.result_classes:
            if isinstance(result, BannerTestResult):
                return result.getDescription(test)
        return self.result_classes[0].getDescription(test)

    def generate_reports(self, test_runner) -> None:
        """Call the generate_report function for all classes in which the
        function is defined.

        :param test_runner: runner class of the test
        """
        for result in self.result_classes:
            if hasattr(result, "generate_reports"):
                result.generate_reports(test_runner)
