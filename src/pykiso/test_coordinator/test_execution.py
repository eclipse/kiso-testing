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
from typing import Any, Dict, List, Optional, Union

import xmlrunner

from ..exceptions import AuxiliaryCreationError, TestCollectionError
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
        for variant, branch in itertools.product(variants, branches):
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
    variants: Optional[tuple] = None,
    branch_levels: Optional[tuple] = None,
    pattern_inject: Optional[str] = None,
    failfast: bool = False,
) -> int:
    """Create test environment based on test configuration.

    :param config: dict from converted YAML config file
    :param report_type: str to set the type of report wanted, i.e. test
        or junit
    :param variants: encapsulate user's variant choices.
    :param branch_levels: encapsulate user's branch level choices.
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
