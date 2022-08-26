##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test Execution
**************

:module: test_execution

:synopsis: Execute a test environment based on the supplied configuration.

.. currentmodule:: test_execute

.. note::
    1. Glob a list of test-suite folders
    2. Generate a list of test-suites with a list of test-cases
    3. Loop per suite
    4. Gather result
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .test_case import BasicTest

import enum
import logging
import sys
import time
import unittest
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import xmlrunner

import pykiso

from ..exceptions import AuxiliaryCreationError, TestCollectionError
from . import test_suite
from .assert_step_report import StepReportData, assert_decorator, generate_step_report
from .test_result import BannerTestResult
from .test_xml_result import XmlTestResult

log = logging.getLogger(__name__)


@enum.unique
class ExitCode(enum.IntEnum):
    """List of possible exit codes"""

    ALL_TESTS_SUCCEEDED = 0
    ONE_OR_MORE_TESTS_FAILED = 1
    ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION = 2
    ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTION = 3
    AUXILIARY_CREATION_FAILED = 4
    BAD_CLI_USAGE = 5


def create_test_suite(
    test_suite_dict: Dict[str, Union[str, int]]
) -> test_suite.BasicTestSuite:
    """create a test suite based on the config dict

    :param test_suite_dict: dict created from config with keys 'suite_dir',
        'test_filter_pattern', 'test_suite_id'
    """
    return test_suite.BasicTestSuite(
        modules_to_add_dir=test_suite_dict["suite_dir"],
        test_filter_pattern=test_suite_dict["test_filter_pattern"],
        test_suite_id=test_suite_dict["test_suite_id"],
        args=[],
        kwargs={},
    )


def apply_tag_filter(
    all_tests_to_run: unittest.TestSuite, usr_tags: Dict[str, List[str]]
) -> None:
    """Filter the test cases based on user tags.

    :param all_tests_to_run: a dict containing all testsuites and testcases
    :param usr_tags: encapsulate user's variant choices
    """

    def is_skip_test(test_case: BasicTest) -> bool:
        """Check if test shall be skipped by evaluating the test case tag
        attribute

        :param test_case: test_case to check
        :return: True if test shall be skipped else False
        """
        for tag_id, tag_value in usr_tags.items():
            if tag_id in test_case.tag.keys():
                items = tag_value if isinstance(tag_value, list) else [tag_value]
                for item in items:
                    if item in test_case.tag[tag_id]:
                        continue
                    else:
                        return True
            else:
                return True
        return False

    def set_skipped(test_case: BasicTest) -> None:
        """Set testcase to skipped

        :param test_case: testcase to be skipped
        """
        test_case.setUp = lambda: "setup_skipped"
        setattr(
            test_case,
            test_case._testMethodName,
            lambda: test_case.skipTest("skipped due to non-matching variant value"),
        )
        test_case.tearDown = lambda: "tearDown_skipped"
        log.info(f"Skip test case: {test_case}")

    base_suite: List[BasicTest] = test_suite.flatten(all_tests_to_run)

    list(map(set_skipped, filter(is_skip_test, base_suite)))


def failure_and_error_handling(result: unittest.TestResult) -> int:
    """provide necessary information to Jenkins if an error occur during tests execution

    :param result: encapsulate all test results from the current run

    :return: an ExitCode object
    """
    failed, errored = result.failures, result.errors
    if failed and errored:
        exit_code = ExitCode.ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTION
    elif failed:
        exit_code = ExitCode.ONE_OR_MORE_TESTS_FAILED
    elif errored:
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    else:
        exit_code = ExitCode.ALL_TESTS_SUCCEEDED
    return exit_code


def enable_step_report(all_tests_to_run: unittest.suite.TestSuite) -> None:
    """Decorate all assert method from Test-Case

        This will allow to save the assert inputs in
        order to generate the step-report

    :param all_tests_to_run: a dict containing all testsuites and testcases
    """
    if sys.version_info.minor >= 8:
        log.warning(
            "Variable names may be missing in the step report when using multiline assert statements on Python >=3.8"
        )

    # Step report header fed during test
    base_suite = test_suite.flatten(all_tests_to_run)
    for tc in base_suite:
        # for any test, show ITF version
        tc.step_report = StepReportData(
            header=OrderedDict({"ITF version": pykiso.__version__})
        )

        # Decorate All assert method
        assert_method_list = [
            method for method in dir(tc) if method.startswith("assert")
        ]
        for method_name in assert_method_list:
            # Get method from name
            method = getattr(tc, method_name)
            # Add decorator to the existing method
            setattr(tc, method_name, assert_decorator(method))


def collect_test_suites(
    config_test_suite_list: List[Dict[str, Union[str, int]]],
    test_filter_pattern: Optional[str] = None,
) -> List[Optional[test_suite.BasicTestSuite]]:
    """Collect and load all test suites defined in the test configuration.

    :param config_test_suite_list: list of dictionaries from the configuration
        file corresponding each to one test suite.
    :param test_filter_pattern: optional filter pattern to overwrite
        the one defined in the test suite configuration.

    :raises pykiso.TestCollectionError: if any test case inside one of
        the configured test suites failed to be loaded.

    :return: a list of all loaded test suites.
    """
    list_of_test_suites = []
    for test_suite_configuration in config_test_suite_list:
        try:
            if test_filter_pattern is not None:
                test_suite_configuration["test_filter_pattern"] = test_filter_pattern
            current_test_suite = create_test_suite(test_suite_configuration)
            list_of_test_suites.append(current_test_suite)
        except BaseException as e:
            raise TestCollectionError(test_suite_configuration["suite_dir"]) from e
    return list_of_test_suites


def execute(
    config: Dict[str, Any],
    report_type: str = "text",
    user_tags: Optional[Dict[str, List[str]]] = None,
    step_report: Optional[Path] = None,
    pattern_inject: Optional[str] = None,
    failfast: bool = False,
) -> int:
    """Create test environment based on test configuration.

    :param config: dict from converted YAML config file
    :param report_type: str to set the type of report wanted, i.e. test
        or junit
    :param user_tags: test case tags to execute
    :param step_report: file path for the step report or None
    :param pattern_inject: optional pattern that will override
        test_filter_pattern for all suites. Used in test development to
        run specific tests.
    :param failfast: stop the test run on the first error or failure.

    :return: exit code corresponding to the result of the test execution
        (tests failed, unexpected exception, ...)
    """
    try:
        test_suites = collect_test_suites(config["test_suite_list"], pattern_inject)
        # Group all the collected test suites in one global test suite
        all_tests_to_run = unittest.TestSuite(test_suites)
        # filter test cases based on variant and branch-level options
        if user_tags:
            apply_tag_filter(all_tests_to_run, user_tags)
        # Enable step report
        if step_report is not None:
            enable_step_report(all_tests_to_run)

        # TestRunner selection: generate or not a junit report. Start the tests and publish the results
        if report_type == "junit":
            junit_report_name = time.strftime("TEST-pykiso-%Y-%m-%d_%H-%M-%S.xml")
            project_folder = Path.cwd()
            reports_path = project_folder / "reports"
            junit_report_path = reports_path / junit_report_name
            reports_path.mkdir(exist_ok=True)
            with open(junit_report_path, "wb") as junit_output:
                test_runner = xmlrunner.XMLTestRunner(
                    output=junit_output,
                    resultclass=XmlTestResult,
                    failfast=failfast,
                )
                result = test_runner.run(all_tests_to_run)
        else:
            test_runner = unittest.TextTestRunner(
                resultclass=BannerTestResult, failfast=failfast
            )
            result = test_runner.run(all_tests_to_run)

        # Generate the html step report
        if step_report is not None:
            generate_step_report(result, step_report)

        exit_code = failure_and_error_handling(result)
    except TestCollectionError:
        log.exception("Error occurred during test collections.")
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    except AuxiliaryCreationError:
        log.exception("Error occurred during auxiliary creation.")
        exit_code = ExitCode.AUXILIARY_CREATION_FAILED
    except KeyboardInterrupt:
        log.exception("Keyboard Interrupt detected")
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    except Exception:
        log.exception(f'Issue detected in the test-suite: {config["test_suite_list"]}!')
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    return int(exit_code)
