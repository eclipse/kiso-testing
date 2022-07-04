##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
ResponseTemplates
*****************

:module: response_templates

:synopsis: Used to create a set of predefined messages

.. currentmodule:: response_templates

.. warning:: Still under test
"""
import random
from typing import List

from pykiso import message
from pykiso.message import Message


class ResponseTemplates:
    """Used to create a set of predefined messages (ACK, NACK, REPORT
    ...)."""

    reasons_list = [
        "Component busy, could not run",
        "fatal error occur, could not run",
        "Overvoltage situation happen, could not run",
    ]
    log = []

    @classmethod
    def default(cls, msg: Message) -> Message:
        """handle default response, if not test case/suite run
        just return ACK message otherwise ACK + REPORT.

        :param msg: current received message

        :return: list of Message
        """

        if (
            msg.sub_type in message.MessageCommandType.__members__.values()
            and msg.sub_type != message.MessageCommandType.PING
            and msg.sub_type != message.MessageCommandType.ABORT
        ):

            return cls.ack_with_report_ok(msg)
        else:
            return cls.ack(msg)

    @classmethod
    def ack(cls, msg: Message) -> List[Message]:
        """Return an acknowledgment message.

        :param msg: current received message

        :return: list of Message
        """
        return [msg.generate_ack_message(message.MessageAckType.ACK)]

    @classmethod
    def ack_with_report_ok(cls, msg: Message) -> List[Message]:
        """Return an acknowledgment message and a report message with
        verdict pass.

        :param msg: current received message

        :return: list of Message
        """
        ack_msg = msg.generate_ack_message(message.MessageAckType.ACK)

        report_msg = message.Message(
            msg_type=message.MessageType.REPORT,
            sub_type=message.MessageReportType.TEST_PASS,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        return [ack_msg, report_msg]

    @classmethod
    def ack_with_report_nok(cls, msg: Message) -> List[Message]:
        """Return an acknowledgment message and a report message with
        verdict failed + tlv part with failure reason.

        :param msg: current received message

        :return: list of Message
        """

        ack_run_cmd = msg.generate_ack_message(message.MessageAckType.ACK)

        report_msg = message.Message(
            msg_type=message.MessageType.REPORT,
            sub_type=message.MessageReportType.TEST_FAILED,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        report_msg.tlv_dict = cls.get_random_reason()

        return [ack_run_cmd, report_msg]

    @classmethod
    def ack_with_logs_and_report_ok(cls, msg: Message) -> List[Message]:
        """Return an acknowledge message and log messages and
        report message with verdict pass.

         :param msg: current received message

         :return: list of Message
        """

        ack_msg = msg.generate_ack_message(message.MessageAckType.ACK)

        log_msg = message.Message(
            msg_type=message.MessageType.LOG,
            sub_type=message.MessageLogType.RESERVED,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        report_msg = message.Message(
            msg_type=message.MessageType.REPORT,
            sub_type=message.MessageReportType.TEST_PASS,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        return [ack_msg, log_msg, log_msg, report_msg]

    @classmethod
    def ack_with_logs_and_report_nok(cls, msg: Message) -> List[Message]:
        """Return an acknowledge message and log messages and
        report message with verdict failed + tlv part with failure reason.

         :param msg: current received message

         :return: list of Message
        """

        ack_msg = msg.generate_ack_message(message.MessageAckType.ACK)

        log_msg = message.Message(
            msg_type=message.MessageType.LOG,
            sub_type=message.MessageLogType.RESERVED,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        report_msg = message.Message(
            msg_type=message.MessageType.REPORT,
            sub_type=message.MessageReportType.TEST_FAILED,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        report_msg.tlv_dict = cls.get_random_reason()

        return [ack_msg, log_msg, log_msg, report_msg]

    @classmethod
    def get_random_reason(self) -> dict:
        """Return tlv dictionary containing a random reason from
        pre-defined reason list.

        :param msg: current received message

        :return: tlv dictionary with failure reason
        """
        return {
            message.TlvKnownTags.FAILURE_REASON: random.choice(
                ResponseTemplates.reasons_list
            )
        }

    @classmethod
    def nack_with_reason(cls, msg: Message) -> List[Message]:
        """Return a NACK message with a tlv part
        containing the failure reason.

        :param msg: current received message

        :return: list of Message
        """
        ack_msg = msg.generate_ack_message(message.MessageAckType.NACK)
        ack_msg.tlv_dict.update(cls.get_random_reason())

        return [ack_msg]

    @classmethod
    def ack_with_report_not_implemented(cls, msg: Message) -> List[Message]:
        """Return an acknowledge message and a report message with
        verdict test not implemented.

        :param msg: current received message

        :return: list of Message
        """

        ack_run_cmd = msg.generate_ack_message(message.MessageAckType.ACK)

        report_msg = message.Message(
            msg_type=message.MessageType.REPORT,
            sub_type=message.MessageReportType.TEST_NOT_IMPLEMENTED,
            test_suite=msg.test_suite,
            test_case=msg.test_case,
        )

        return [ack_run_cmd, report_msg]
