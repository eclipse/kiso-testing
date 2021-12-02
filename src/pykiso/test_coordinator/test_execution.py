##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
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

import enum
import logging
import time
import unittest
from pathlib import Path
from typing import Dict

import xmlrunner

from . import test_suite
from .test_xml_result import XmlTestResult

log = logging.getLogger(__name__)


@enum.unique
class ExitCode(enum.IntEnum):
    """List of possible exit codes"""

    ALL_TESTS_SUCCEEDED = 0
    ONE_OR_MORE_TESTS_FAILED = 1
    ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION = 2
    ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTION = 3


def create_test_suite(test_suite_dict: Dict) -> test_suite.BasicTestSuite:
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


def failure_and_error_handling(result):
    """provide necessary information to Jenkins if an error occur during tests execution

    :param result: a unittest.TestResult object
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


def execute(config: Dict, report_type: str = "text"):

    """create test environment base on config

    :param config: dict from converted YAML config file
    :param report_type: str to set the type of report wanted, i.e. test or junit
    """
    try:
        list_of_test_suites = []
        for test_suite_configuration in config["test_suite_list"]:
            try:
                list_of_test_suites.append(create_test_suite(test_suite_configuration))
            except BaseException:
                break

        # Collect all the tests in one global test suite
        all_tests_to_run = unittest.TestSuite(list_of_test_suites)
        # TestRunner selection: generate or not a junit report. Start the tests and publish the results
        if report_type == "junit":
            junit_report_name = time.strftime("TEST-pykiso-%Y-%m-%d_%H-%M-%S.xml")
            project_folder = Path.cwd()
            reports_path = project_folder / "reports"
            junit_report_path = reports_path / junit_report_name
            reports_path.mkdir(exist_ok=True)
            with open(junit_report_path, "wb") as junit_output:
                test_runner = xmlrunner.XMLTestRunner(
                    output=junit_output, resultclass=XmlTestResult
                )
                result = test_runner.run(all_tests_to_run)
        else:
            test_runner = unittest.TextTestRunner()
            result = test_runner.run(all_tests_to_run)
        exit_code = failure_and_error_handling(result)

    except KeyboardInterrupt:
        log.exception("Keyboard Interrupt detected")
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    except Exception:
        log.exception(f'Issue detected in the test-suite: {config["test_suite_list"]}!')
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    finally:
        return int(exit_code)
