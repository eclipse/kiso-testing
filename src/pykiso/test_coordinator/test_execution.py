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
import enum
import itertools
import logging
import time
import unittest
from pathlib import Path
from typing import Dict, Optional

import xmlrunner

from ..exceptions import AuxiliaryCreationError
from . import test_suite
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


def apply_variant_filter(
    all_tests_to_run: dict, variants: tuple, branch_levels: tuple
) -> None:
    """Filter the test cases based on the variant string.

    :param all_tests_to_run: a dict containing all testsuites and testcases
    :param variants: encapsulate user's variant choices
    :param branch_levels: encapsulate user's branch level choices
    """

    def tag_present(tag_list: tuple, tc_tags: list) -> bool:
        """Determine if at least branch_level or variant tag is present
        at test fixture decorator level.

        :param tag_list: encapsulate user's variant choices
        :param tc_tags: encapsulate all available tags on test case
            decorator level

        :return: True if a variant or branch_level is found
            otherwise False
        """
        for tag in tag_list:
            if tag in tc_tags:
                return True
        else:
            return False

    def both_present(variants: tuple, branches: tuple, tc_tags: list) -> bool:
        """Determine if the couple branch_level and variant is present
        at test fixture decorator level.

        :param variants: encapsulate user's variant choices
        :param branches: encapsulate user's branch level choices
        :param tc_tags: encapsulate all available tags on test case
            decorator level

        :return: True if a couple variant/branch_level is found
            otherwise False
        """
        for variant in variants:
            for branch in branches:
                if variant in tc_tags and branch in tc_tags:
                    return True
        else:
            return False

    base_suite = test_suite.flatten(all_tests_to_run)
    both_given = variants and branch_levels

    for tc in base_suite:
        # if variant at decorator level is not given just run it
        if tc.tag is not None:
            # extract variant and branch from test fixture
            tc_variants = tc.tag.get("variant", list())
            tc_branches = tc.tag.get("branch_level", list())
            tc_tags = list(itertools.chain(tc_variants, tc_branches))

            # if user gives both branch and variant filter using couple
            # (variant, branch_level)
            if both_given and both_present(variants, branch_levels, tc_tags):
                continue
            # user gives only variant param, filter using only variant
            elif not both_given and tag_present(variants, tc_tags):
                continue
            # user gives only branch param, filter using only branch
            elif not both_given and tag_present(branch_levels, tc_tags):
                continue
            # the test is not intended to be run skip it
            else:
                tc.setUp = lambda: "setup_skipped"
                setattr(
                    tc,
                    tc._testMethodName,
                    lambda: tc.skipTest("skipped due to non-matching variant value"),
                )
                tc.tearDown = lambda: "tearDown_skipped"


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


def execute(
    config: Dict,
    report_type: str = "text",
    variants: Optional[tuple] = None,
    branch_levels: Optional[tuple] = None,
    pattern_inject: Optional[str] = None,
    failfast: bool = False,
) -> int:
    """create test environment base on config

    :param config: dict from converted YAML config file
    :param report_type: str to set the type of report wanted, i.e. test
        or junit
    :param variants: encapsulate user's variant choices
    :param branch_levels: encapsulate user's branch level choices
    :param pattern_inject: optional pattern that will override
        test_filter_pattern for all suites. Used in test development to
        run specific tests.
    :param failfast: Stop the test run on the first error or failure

    :return: exit code corresponding to the actual tets exeuciton run
        state(tests failed, unexpected exception...)
    """
    exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    is_raised = False

    try:
        list_of_test_suites = []
        for test_suite_configuration in config["test_suite_list"]:
            try:
                if pattern_inject is not None:
                    test_suite_configuration["test_filter_pattern"] = pattern_inject
                list_of_test_suites.append(create_test_suite(test_suite_configuration))
            except BaseException:
                is_raised = True
                break

        # Collect all the tests in one global test suite
        all_tests_to_run = unittest.TestSuite(list_of_test_suites)
        if variants or branch_levels:
            apply_variant_filter(all_tests_to_run, variants, branch_levels)
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

        # if an exception is raised during test suite collections at least
        # return exit code ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
        if is_raised:
            exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
        else:
            exit_code = failure_and_error_handling(result)
    except AuxiliaryCreationError:
        exit_code = ExitCode.AUXILIARY_CREATION_FAILED
    except KeyboardInterrupt:
        log.exception("Keyboard Interrupt detected")
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    except Exception:
        log.exception(f'Issue detected in the test-suite: {config["test_suite_list"]}!')
        exit_code = ExitCode.ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
    finally:
        return int(exit_code)
