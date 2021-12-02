##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Generic Test
************

:module: test_case

:synopsis: Basic extensible implementation of a TestCase.

.. currentmodule:: test_case

.. note:: TODO later on will inherit from a metaclass to get the id parameters
"""

import functools
import logging
import unittest
from typing import List, Optional, Type, Union

from .. import message
from ..auxiliary import AuxiliaryInterface
from ..cli import get_logging_options, initialize_logging
from .test_message_handler import TestCaseMsgHandler

log = logging.getLogger(__name__)


class BasicTest(unittest.TestCase):
    """Base for test-cases."""

    msg_handler: Type[TestCaseMsgHandler] = TestCaseMsgHandler
    response_timeout: int = 10

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
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
        """
        # Initialize base class
        super().__init__(*args, **kwargs)
        # Save list of test auxiliaries to use (already initialize)
        self.test_auxiliary_list = aux_list or []
        # Save test information
        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id
        self.setup_timeout = setup_timeout or BasicTest.response_timeout
        self.run_timeout = run_timeout or BasicTest.response_timeout
        self.teardown_timeout = teardown_timeout or BasicTest.response_timeout
        self.test_ids = test_ids

    def cleanup_and_skip(self, aux: AuxiliaryInterface, info_to_print: str) -> None:
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

    @classmethod
    def setUpClass(cls) -> None:
        """A class method called before tests in an individual class are
        run.

        This implementation is only mandatory to enable logging in junit
        report. The logging configuration has to be call inside test
        runner run, otherwise stdout is never caught.
        """
        options = get_logging_options()
        if options.report_type == "junit":
            initialize_logging(None, options.log_level, options.report_type)

    def setUp(self) -> None:
        """Hook method for constructing the test fixture."""
        log.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # lock auxiliaries
        for aux in self.test_auxiliary_list:
            locked = aux.lock_it(1)
            if not locked:
                self.cleanup_and_skip(aux, f"{aux} could not be locked!")

        # send TEST_CASE_RUN command wait for report and log it
        with self.msg_handler.setup(
            test_entity=self,
            timeout_cmd=5,
            timeout_resp=self.setup_timeout,
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

    # @timeout_decorator.timeout(5) # Timeout of 10 second as generic test-case # TODO: Only working on linux
    def test_run(self) -> None:
        """Hook method from unittest in order to execute test case."""
        log.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # lock auxiliaries
        for aux in self.test_auxiliary_list:
            locked = aux.lock_it(1)
            if not locked:
                self.cleanup_and_skip(aux, f"{aux} could not be locked!")

        # send TEST_CASE_RUN command wait for report and log it
        with self.msg_handler.run(
            test_entity=self,
            timeout_cmd=5,
            timeout_resp=self.run_timeout,
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

    def tearDown(self) -> None:
        """Hook method for deconstructing the test fixture after testing it."""
        log.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # lock auxiliaries
        for aux in self.test_auxiliary_list:
            locked = aux.lock_it(1)
            if not locked:
                self.cleanup_and_skip(aux, f"{aux} could not be locked!")

        # send TEST_CASE_TEARDOWN command wait for report and log it
        with self.msg_handler.teardown(
            test_entity=self,
            timeout_cmd=5,
            timeout_resp=self.teardown_timeout,
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


def define_test_parameters(
    suite_id: int = 0,
    case_id: int = 0,
    aux_list: List[AuxiliaryInterface] = None,
    setup_timeout: Optional[int] = None,
    run_timeout: Optional[int] = None,
    teardown_timeout: Optional[int] = None,
    test_ids: Optional[dict] = None,
):
    """Decorator to fill out test parameters of the BasicTest automatically."""

    def generate_modified_class(DecoratedClass):
        """Generates the same class but with the test IDs already filled.
        It works as a partially filled-out call to the __init__ method.
        """

        class NewClass(DecoratedClass):
            """Modified {DecoratedClass.__name__}, with the __init__ method
            already filled out with the following test-parameters:

            Suite ID:    {suite_id}
            Case ID:     {case_id}
            Auxiliaries: {auxes}
            setup_timeout: {setup_timeout}
            run_timeout: {run_timeout}
            teardown_timeout: {teardown_timeout}
            test_ids: {test_ids}
            """

            @functools.wraps(DecoratedClass.__init__)
            def __init__(self, *args, **kwargs):
                super(NewClass, self).__init__(
                    suite_id,
                    case_id,
                    aux_list,
                    setup_timeout,
                    run_timeout,
                    teardown_timeout,
                    test_ids,
                    args,
                    kwargs,
                )

        NewClass.__doc__ = NewClass.__doc__.format(
            DecoratedClass=DecoratedClass,
            suite_id=suite_id,
            case_id=case_id,
            auxes=[aux.__class__.__name__ for aux in aux_list or []],
            setup_timeout=setup_timeout,
            run_timeout=run_timeout,
            teardown_timeout=teardown_timeout,
            test_ids=test_ids,
        )
        # Passing the name of the decorated class to the new returned class
        # in order to get the test case name and references, i.e. suite_id and case_id
        # in the test results in the console and in the report.
        # Changing __name__ is necessary to make the test name appear in the test results in the console.
        # Changing __qualname__ is necessary to make the test name appear in the test results in the report.
        NewClass.__name__ = DecoratedClass.__name__ + f"-{suite_id}-{case_id}"
        NewClass.__qualname__ = DecoratedClass.__qualname__ + f"-{suite_id}-{case_id}"

        return NewClass

    return generate_modified_class
