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

When using a Remote TestCase/TestSuite, the integration test framework handles 
internal messaging and control flow using a message format defined in
:py:class:`pykiso.Message`. :py:mod:`pykiso.test_message_handler`
defines the messaging protocol from a behavioral point of view.

The general procedure is described in handle_basic_interaction context
manager, but specific _MsgHandler_ classes are  provided with
:py:class:`TestCaseMsgHandler` and :py:class:`TestSuiteMsgHandler` to
provide shorthands for the specialised communication from
:py:class:`pykiso.test_case.RemoteTest` and
:py:class:`pykiso.test_suite.RemoteTestSuite`.


:module: test_message_handler

:synopsis: default communication between TestManagement and DUT.

.. currentmodule:: test_message_handler

"""
import collections
import functools
import logging
from contextlib import contextmanager
from typing import Callable, List

from pykiso import message

__all__ = [
    "report_analysis",
    "handle_basic_interaction",
    "test_app_interaction",
]

report_analysis = collections.namedtuple(
    "report_analysis",
    ["current_auxiliary", "report_message", "logging_method", "log_message"],
)

cmd_response = collections.namedtuple(
    "cmd_response", ["valid", "sent_command", "current_auxiliary"]
)

wait_report = collections.namedtuple("wait_report", ["current_auxiliary", "message"])

log = logging.getLogger(__name__)


@contextmanager
def handle_basic_interaction(
    test_entity: Callable,
    cmd_sub_type: message.MessageCommandType,
    timeout_cmd: int,
    timeout_resp: int,
) -> List[report_analysis]:
    """Handle default communication mechanism between test manager and device under
    test as follow:

    .. code-block:: none

       TM |   COMMAND ---------->        | DUT
       TM |           <---------- ACK    | DUT
       TM |           <---------- LOG    | DUT
       TM |   ACK     ---------->        | DUT
       ...
       TM |           <---------- LOG    | DUT
       TM |   ACK     ---------->        | DUT
       TM |           <---------- REPORT | DUT
       TM |   ACK     ---------->        | DUT

    This behaviour is implemented here.

    Logs can be sent to TM while waiting for report.

    :param test_entity: test instance in use (BaseTestSuite, BasicTest,...)
    :param cmd_sub_type: message command sub-type (Test case run, setup,....)
    :param timeout_cmd: timeout in seconds for auxiliary run_command
    :param timeout_resp: timeout in seconds for auxiliary wait_and_get_report

    :return: tuple containing current auxiliary, reported message, logging method to use,
        and pre-defined log message.
    """
    responses = []
    # send command and check if DUT response is correctly received
    with Command.send(
        cmd_sub_type=cmd_sub_type, test_entity=test_entity, timeout_cmd=timeout_cmd
    ) as cmd_responses:

        for cmd_execution in cmd_responses:
            if not cmd_execution.valid:
                info_to_print = f"No response received from DUT for auxiliairy : {cmd_execution.current_auxiliary} command : {cmd_execution.sent_command}!"
                test_entity.cleanup_and_skip(
                    cmd_execution.current_auxiliary, info_to_print
                )

            # wait for DUT log and report and evaluate the response
            # while loop to wait for reports while getting the logs
            else:
                report_received = False
                while not report_received:
                    received_msg = cmd_execution.current_auxiliary.wait_and_get_report(
                        blocking=True, timeout_in_s=timeout_resp
                    )
                    if received_msg is None:
                        info_to_print = (
                            f"No report received from DUT for auxiliairy : {cmd_execution.current_auxiliary} command :{cmd_execution.sent_command}!",
                        )
                        test_entity.cleanup_and_skip(
                            cmd_execution.current_auxiliary, info_to_print
                        )
                        break
                    if received_msg.get_message_type() == message.MessageType.REPORT:
                        report_received = True
                    responses.append(
                        Command.evaluate_message(
                            cmd_execution.current_auxiliary, received_msg
                        )
                    )

    yield responses


class Command:
    """Encapsulate message command handling"""

    @classmethod
    @contextmanager
    def send(
        cls,
        test_entity: Callable,
        cmd_sub_type: message.MessageCommandType,
        timeout_cmd: int,
    ):
        """Used to send a specific message command to device under test for
        all current auxiliaries in use.

        :param test_entity: test instance in use (BaseTestSuite, BasicTest,...)
        :param cmd_sub_type: message command sub-type (Test case run, setup,....)
        :param timeout_cmd: timeout in second apply on auxiliary run_command

        :return: generator with namedtuple containing run_command verdict,
            command sent, and current auxiliary in use.
        """

        cmd = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=cmd_sub_type,
            test_suite=test_entity.test_suite_id,
            test_case=test_entity.test_case_id,
        )
        responses = []
        for aux in test_entity.test_auxiliary_list:
            if not aux.stop_event.is_set():
                _response = aux.run_command(
                    cmd, blocking=True, timeout_in_s=timeout_cmd
                )
                responses.append(cmd_response(_response, cmd, aux))
            else:
                log.fatal(f"Auxiliary {aux} is stopped")
                test_entity.fail(
                    f"Auxiliary {aux} is stopped: test suite id: {test_entity.test_suite_id}, test case id: {test_entity.test_case_id}"
                )
        yield responses

    @classmethod
    def evaluate_message(cls, aux, report_msg: message.Message) -> report_analysis:
        """Evaluate message type coming from DUT (COMMAND, LOG, REPORT...)

        :param aux: current auxiliary in use
        :param report_msg: message received from DUT

        :return: namedtuple containing current auxiliary, reported message, logging method to use,
            and pre-defined log message.
        """

        if report_msg.get_message_type() == message.MessageType.REPORT:
            return Report.evaluate_report(aux, report_msg)

        elif report_msg.get_message_type() == message.MessageType.LOG:
            log_msg = f"Logging message received from {aux.name},  : {report_msg}"
            return report_analysis(aux, report_msg, log.info, log_msg)
        else:
            log_msg = f"Message type unknown received from {aux.name},  : {report_msg}"
            return report_analysis(aux, report_msg, log.warning, log_msg)


class Report:
    """Manage Test App report."""

    @classmethod
    @contextmanager
    def wait(cls, auxiliaries, timeout: int):
        """Used to wait deveice under test's message command report.

        :param auxiliaries: auxiliar(y/ies) in use
        :param timeout: timeout in second apply on auxiliary wait_and_get_report

        :return: generator with namedtuple containing current auxiliary and current
            message from device under test(if timeout reach None otherwise Message instance)
        """

        for aux in auxiliaries:
            _report = aux.wait_and_get_report(blocking=True, timeout_in_s=timeout)
            yield wait_report(aux, _report)

    @classmethod
    def evaluate_report(cls, aux, report_msg: message.Message):
        """Evaluate message command report content (PASS, FAILED, NOT IMPLEMENTED)

        :param aux: current auxiliary in use
        :param report_msg: message received from DUT

        :return: namedtuple containing current auxiliary, reported message, logging method to use,
            and pre-defined log message.
        """
        log_fun = None
        log_msg = None
        if report_msg.get_message_sub_type() == message.MessageReportType.TEST_FAILED:
            log_fun = log.error
            log_msg = (
                f"Report with verdict FAILED received from {aux.name} : {report_msg}"
            )
        elif report_msg.get_message_sub_type() == message.MessageReportType.TEST_PASS:
            log_fun = log.info
            log_msg = (
                f"Report with verdict PASS received from {aux.name} : {report_msg}"
            )

        elif (
            report_msg.get_message_sub_type()
            == message.MessageReportType.TEST_NOT_IMPLEMENTED
        ):
            log_fun = log.info
            log_msg = (
                f"Report with verdict NOT IMPLEMENTED from {aux.name} : {report_msg}"
            )
        else:
            log_fun = log.warning
            log_msg = f"Report type unknown received from {aux.name} : {report_msg}"

        return report_analysis(aux, report_msg, log_fun, log_msg)


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

            # lock auxiliaries
            for aux in self.test_auxiliary_list:
                locked = aux.lock_it(1)
                if not locked:
                    self.cleanup_and_skip(aux, f"{aux} could not be locked!")

            with handle_basic_interaction(
                self, message_type, timeout_cmd, timeout_resp
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
                    is_report = (
                        report_msg.get_message_type() == message.MessageType.REPORT
                    )
                    if is_test_on_dut_implemented and is_report:
                        self.assertEqual(
                            report_msg.sub_type, message.MessageReportType.TEST_PASS
                        )

            return func(self, *args, **kwargs)

        return handle_interaction

    return inner_interaction
