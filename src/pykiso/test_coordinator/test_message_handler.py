##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Handle common communication with device under test
**************************************************

When using a Remote TestCase/TestSuite, the integration test framework
handles internal messaging and control flow using a message format
defined in :py:class:`pykiso.Message`.

:py:mod:`pykiso.test_message_handler` defines the messaging protocol
from a behavioral point of view.

:module: test_message_handler

:synopsis: default communication between TestManagement and DUT.

.. currentmodule:: test_message_handler

"""

import functools
import logging
from typing import Callable

from pykiso import message

log = logging.getLogger(__name__)


def test_app_interaction(
    message_type: message.MessageCommandType, timeout_cmd: int = 5
) -> Callable:
    """Handle test app basic interaction depending on the decorated
    method.

    :param message_type: message command sub-type (test case/suite
        run, setup, teardown....)
    :param timeout_cmd: timeout in seconds for auxiliary run_command

    :return: inner decorator function
    """

    def inner_interaction(func: Callable) -> Callable:
        """Inner decorator function.

        :param func: decorated method

        :return: decorator inner function
        """

        @functools.wraps(func)
        def handle_interaction(self, *args: tuple, **kwargs: dict) -> None:
            """Handle Test App communication mechanism during for all
            available fixtures(setup, run, teardown,...)

            :param args: positional arguments
            :param kwargs: named arguments

            :return: decorated method return (actual case None)
            """

            fixture = func.__name__.lower()

            if "setup" in fixture and "suite" in fixture:
                log.info(
                    f"--------------- SUITE SETUP: {self.test_suite_id} ---------------"
                )
                timeout_resp = self.setup_timeout
            elif "setup" in fixture:
                log.info(
                    f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
                )
                timeout_resp = self.setup_timeout
            elif "run" in fixture:
                log.info(
                    f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
                )
                timeout_resp = self.run_timeout
            elif "teardown" in fixture and "suite" in fixture:
                log.info(
                    f"--------------- SUITE TEARDOWN: {self.test_suite_id} ---------------"
                )
                timeout_resp = self.teardown_timeout
            elif "teardown" in fixture:
                log.info(
                    f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
                )
                timeout_resp = self.teardown_timeout

            # for all configured auxiliaries just send the associated
            # command and evaluate return test results
            for aux in self.test_auxiliary_list:

                cmd = message.Message(
                    msg_type=message.MessageType.COMMAND,
                    sub_type=message_type,
                    test_suite=self.test_suite_id,
                    test_case=self.test_case_id,
                )
                is_ack = aux.send_fixture_command(command=cmd, timeout=timeout_cmd)

                # if the DUT has not acknowledge, just abort and try to
                # create a brand new communication stream with it
                if is_ack is False:
                    info_to_print = f"No response received from DUT for auxiliairy : {aux} command : {cmd}!"
                    self.cleanup_and_skip(aux, info_to_print)

                # wait until the DUT has run the required test fixture
                report = aux.wait_and_get_report(
                    blocking=True, timeout_in_s=timeout_resp
                )

                # no report was received during the defined time slot,
                # just abort and try to create a brand new communication
                # stream
                if report is None:
                    info_to_print = (
                        f"No report received from DUT for auxiliairy : {aux} command :{cmd}!",
                    )
                    self.cleanup_and_skip(aux, info_to_print)

                is_test_on_dut_implemented = (
                    report.sub_type != message.MessageReportType.TEST_NOT_IMPLEMENTED
                )
                is_report = report.get_message_type() == message.MessageType.REPORT

                # At least the test has to be implemented at embedded
                # side and a report type command was received
                if is_test_on_dut_implemented and is_report:
                    self.assertEqual(
                        report.sub_type, message.MessageReportType.TEST_PASS
                    )

            return func(self, *args, **kwargs)

        return handle_interaction

    return inner_interaction
