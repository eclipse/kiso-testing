##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test Suite
**********

:module: test_suite

:synopsis: Create a generic test-suite based on the connected modules

.. currentmodule:: generic_test_suite


"""

import logging
import unittest
from collections.abc import Iterable
from typing import Callable, List, Union

from .. import message
from ..interfaces.thread_auxiliary import AuxiliaryInterface
from .test_message_handler import TestSuiteMsgHandler, handle_basic_interaction

__all__ = [
    "BaseTestSuite",
    "BasicTestSuiteSetup",
    "BasicTestSuiteTeardown",
    "BasicTestSuite",
    "TestSuiteMsgHandler",
]

log = logging.getLogger(__name__)


class BaseTestSuite(unittest.TestCase):

    response_timeout = 10

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
        variant: Union[list, None],
        args: tuple,
        kwargs: dict,
    ):
        """Initialize generic test-case.

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used auxiliaries
        :param setup_timeout: maximum time (in seconds) used to wait
            for a report during setup execution
        :param run_timeout: maximum time (in seconds) used to wait for
            a report during test_run execution
        :param teardown_timeout: the maximum time (in seconds) used to
            wait for a report during teardown execution
        :param test_ids: jama references to get the coverage
            eg: {"Component1": ["Req1", "Req2"], "Component2 ["Req3"]}
        :param variant: string that allows the user to execute a subset of tests
        """
        # Initialize base class
        super().__init__(*args, **kwargs)
        # Save test information
        self.test_auxiliary_list = aux_list or []
        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id
        self.setup_timeout = setup_timeout or BaseTestSuite.response_timeout
        self.run_timeout = run_timeout or BaseTestSuite.response_timeout
        self.teardown_timeout = teardown_timeout or BaseTestSuite.response_timeout
        self.test_ids = test_ids
        self.variant = variant

    def cleanup_and_skip(self, aux: AuxiliaryInterface, info_to_print: str):
        """Cleanup auxiliary and log reasons.

        :param aux: corresponding auxiliary to abort
        :param info_to_print: A message you want to print while cleaning up the test
        """
        # Log error message
        log.critical(info_to_print)

        # Send aborts to corresponding auxiliary
        if aux.abort_command() is not True:
            log.critical(f"Error occurred during abort command on auxiliary {aux}")

        self.fail(info_to_print)

    def base_function(
        self,
        current_fixture: Callable,
        step_name: str,
        test_command: message.Message,
        timeout_resp: int,
    ):
        """Base function used for test suite setup and teardown.

        :param current_fixture: fixture instance teardown or setup
        :param step_name: name of the current step
        :param test_command: A message you want to print while cleaning up the test
        :param timeout_resp: maximum amount of time in seconds to wait
            for a response
        """
        log.info(f"--------------- {step_name}: {self.test_suite_id} ---------------")

        # lock auxiliaries
        for aux in self.test_auxiliary_list:
            locked = aux.lock_it(1)
            if not locked:
                self.cleanup_and_skip(aux, f"{aux} could not be locked!")

        # send TEST_SUITE_SETUP or TEST_SUITE_TEARDOWN command wait for report and log it
        with handle_basic_interaction(
            test_entity=current_fixture,
            cmd_sub_type=test_command,
            timeout_cmd=5,
            timeout_resp=timeout_resp,
        ) as report_infos:

            # Unlock all auxiliaries
            for aux in self.test_auxiliary_list:
                aux.unlock_it()

            for aux, report_msg, log_level_func, log_msg in report_infos:
                log_level_func(log_msg)

                is_test_on_dut_implemented = (
                    report_msg.sub_type
                    != message.MessageReportType.TEST_NOT_IMPLEMENTED
                )
                is_report = report_msg.get_message_type() == message.MessageType.REPORT
                if is_test_on_dut_implemented and is_report:
                    self.assertEqual(
                        report_msg.sub_type, message.MessageReportType.TEST_PASS
                    )


class BasicTestSuiteSetup(BaseTestSuite):
    """Inherit from unittest testCase and represent setup fixture."""

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
        variant: Union[list, None],
        args: tuple,
        kwargs: dict,
    ):
        """Initialize generic test-case.

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used auxiliaries
        :param setup_timeout: maximum time (in seconds) used to wait
            for a report during setup execution
        :param run_timeout: maximum time (in seconds) used to wait for
            a report during test_run execution
        :param teardown_timeout: the maximum time (in seconds) used to
            wait for a report during teardown execution
        :param test_ids: jama references to get the coverage
            eg: {"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}
        :param variant: string that allows the user to execute a subset of tests
        """
        # Initialize base class
        super().__init__(
            test_suite_id,
            test_case_id,
            aux_list,
            setup_timeout,
            run_timeout,
            teardown_timeout,
            test_ids,
            variant,
            args,
            kwargs,
        )

    def test_suite_setUp(self):
        """Test method for constructing the actual test suite."""
        self.base_function(
            self,
            "SUITE SETUP",
            message.MessageCommandType.TEST_SUITE_SETUP,
            self.setup_timeout,
        )


class BasicTestSuiteTeardown(BaseTestSuite):
    """Inherit from unittest testCase and represent teardown fixture."""

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
        variant: Union[list, None],
        args: tuple,
        kwargs: dict,
    ):
        """Initialize generic test-case.

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used auxiliaries
        :param setup_timeout: maximum time (in seconds) used to wait
            for a report during setup execution
        :param run_timeout: maximum time (in seconds) used to wait for
            a report during test_run execution
        :param teardown_timeout: the maximum time (in seconds) used to
            wait for a report during teardown execution
        :param test_ids: jama references to get the coverage
            eg: {"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}
        :param variant: string that allows the user to execute a subset of tests
        """
        # Initialize base class
        super().__init__(
            test_suite_id,
            test_case_id,
            aux_list,
            setup_timeout,
            run_timeout,
            teardown_timeout,
            test_ids,
            variant,
            args,
            kwargs,
        )

    def test_suite_tearDown(self):
        """Test method for deconstructing the actual test suite after testing it."""
        self.base_function(
            self,
            "SUITE TEARDOWN",
            message.MessageCommandType.TEST_SUITE_TEARDOWN,
            self.teardown_timeout,
        )


class BasicTestSuite(unittest.TestSuite):
    """Inherit from the unittest framework test-suite but build it for our integration tests."""

    def __init__(
        self,
        modules_to_add_dir: str,
        test_filter_pattern: str,
        test_suite_id: int,
        args: tuple,
        kwargs: dict,
    ):
        """Initialize our custom unittest-test-suite.

        .. note:
            1. Will Load from the given path the integration test modules under test
            2. Sort the given test case list by test suite/case id
            3. Place Test suite setup and teardown respectively at top and bottom of test case list
            4. Add sorted test case list to test suite
        """
        # Mother class initialization
        super().__init__(*args, **kwargs)

        # load test from the specified folder
        loader = unittest.TestLoader()
        found_modules = loader.discover(modules_to_add_dir, pattern=test_filter_pattern)

        # sort the test case list by ascendant using test suite and test case id
        test_case_list = sorted(flatten(found_modules), key=tc_sort_key)

        # add sorted test case list to test suite
        self.addTests(test_case_list)


def tc_sort_key(tc):
    """Sort-key for testcases.

    will sort by test-suite/test-case, but the setup will always be first,
    the teardown will always be last.

    :param tc: a BaseTestSuite/TestCase to rank

    :return: key for :py:func:`sorted`

    :raise: any exception that occurs during test loading
    """
    try:
        fix_ind = 0
        if isinstance(tc, BasicTestSuiteSetup):
            fix_ind = -1
        elif isinstance(tc, BasicTestSuiteTeardown):
            fix_ind = 1
        elif isinstance(tc, unittest.loader._FailedTest):
            raise tc._exception
        return (fix_ind, tc.test_suite_id, tc.test_case_id)
    except BaseException:
        log.exception("Issue detected during test suite initialization!")


def flatten(it):
    """Flatten all level of nesting.

    :param it: nested iterable

    :return: first not nested items
    """
    for x in it:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x
