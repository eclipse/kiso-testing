##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Device Under Test Auxiliary
***************************

:module: DUTAuxiliary

:synopsis: The Device Under Test auxiliary allow to flash and run test
    on the target using the connector provided.

.. currentmodule:: dut_auxiliary

"""
from __future__ import annotations

import functools
import logging
import queue
from typing import Callable, Optional

from pykiso import CChannel, Flasher, Message, message
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    flash_target,
    open_connector,
)

log = logging.getLogger(__name__)

MESSAGE_TYPE = message.MessageType
COMMAND_TYPE = message.MessageCommandType
REPORT_TYPE = message.MessageReportType


def retry_command(tries: int) -> Callable:
    """Force to resend the command a define number of times in case of
    failure.

    :param tries: maximum number of try to get the acknowledgement from
        the DUT

    :return: inner decorator function
    """

    def inner_retry(func: Callable) -> Callable:
        """Inner decorator function.

        :param func: decorated method

        :return: decorator inner function
        """

        @functools.wraps(func)
        def handle_ack(*arg: tuple, **kwargs: dict) -> bool:
            """Based on the run_command method return, just resend the
            command.

            :param arg: positional arguments
            :param kwargs: named arguments

            :return: True if the command was acknowledged otherwise
                False
            """
            for idx in range(tries):
                log.internal_info(f"command try n: {idx}")
                if func(*arg, **kwargs):
                    return True
            return False

        return handle_ack

    return inner_retry


def check_acknowledgement(func: Callable) -> Callable:
    """Check ifthe DUT has acknowledge the previous sent command.

    :param func: decorated method

    :return: decorator inner function
    """

    def inner_check(self, *arg: tuple, **kwargs: dict) -> bool:
        """Check if an ACK message was received and if the token is
        valid.

        :param self: aux instance
        :param arg: positional arguments
        :param kwargs: named arguments

        :return: True if the command was acknowledged otherwise
            False
        """
        response = func(self, *arg, **kwargs)

        # nothing was received
        if response is None:
            log.error("Nothing received from the DUT for the current request!")
            return False

        is_ack = self.current_cmd.check_if_ack_message_is_matching(response)

        # invalid token or received message not type of ACK
        if is_ack is False:
            log.internal_warning(
                f"Received {response} not matching {self.current_cmd}!"
            )
            return False

        log.internal_info("Command was acknowledged by the DUT!")
        return True

    return inner_check


def restart_aux(func: Callable) -> Callable:
    """Force he auxiliary restart if the command is not acknowledge

    :param func: decorated method

    :return: decorator inner function
    """

    def inner_start(self, *arg: tuple, **kwargs: dict) -> bool:
        """Based on the run_command method return, force the auxiliary
        to create a brand new communication stream with the DUT (call of
        delete/create instance).

        :param self: aux instance
        :param arg: positional arguments
        :param kwargs: named arguments

        :return: True if the command was acknowledged otherwise
            False
        """
        state = func(self, *arg, **kwargs)

        # restart the whole auxiliary to have a brand new connection
        # with the DUT
        if state is False:
            self.delete_instance()
            self.create_instance()
        return state

    return inner_start


class DUTAuxiliary(DTAuxiliaryInterface):
    """Device Under Test(DUT) auxiliary implementation."""

    def __init__(
        self,
        com: CChannel = None,
        flash: Flasher = None,
        **kwargs,
    ):
        """Constructor.

        :param name: Alias of the auxiliary instance
        :param com: Communication connector
        :param flash: flash connector
        """
        super().__init__(
            is_proxy_capable=False, tx_task_on=True, rx_task_on=True, **kwargs
        )
        self.channel = com
        self.flash = flash
        self.current_cmd = None

    @retry_command(tries=1)
    @check_acknowledgement
    def send_ping_command(self, timeout: int) -> bool:
        """Send ping command to the DUT.

        :param timeout: how long to wait for an acknowledgement from the
            DUT (seconds)

        :return: True if the command is acknowledged otherwise False
        """

        # TODO: remove it when DUT start sending message at start-up
        # clean the reception queue due to a bug on embedded TestApp,
        while not self.queue_out.empty():
            self.queue_out.get_nowait()

        self.current_cmd = message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.PING)
        log.internal_info(f"send ping request: {self.current_cmd}")
        return self.run_command(
            cmd_message=self.current_cmd,
            cmd_data=None,
            blocking=True,
            timeout_in_s=timeout,
        )

    @retry_command(tries=2)
    @check_acknowledgement
    def send_fixture_command(self, command: message.Message, timeout: int) -> bool:
        """Send command related to test execution (test case setup,
        test case run...) to the DUT.

        :param command: command to execute on DUT side
        :param timeout: how long to wait for an acknowledgement from the
            DUT (seconds)

        :return: True if the command is acknowledged otherwise False
        """
        self.current_cmd = command
        log.internal_info(f"send request: {self.current_cmd}")
        return self.run_command(
            cmd_message=self.current_cmd,
            cmd_data=None,
            blocking=True,
            timeout_in_s=timeout,
        )

    @retry_command(tries=2)
    @restart_aux
    @check_acknowledgement
    def send_abort_command(self, timeout: int):
        """Send abort command to the DUT.

        .. warning:: if the DUT doesn't acknowledge to the abort command
            the auxiliary is restarted, a brand new connection is
            established

        :param timeout: how long to wait for an acknowledgement from the
            DUT (seconds)

        :return: True if the command is acknowledged otherwise False
        """
        self.current_cmd = message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.ABORT)
        log.internal_info(f"send abort request: {self.current_cmd}")
        return self.run_command(
            cmd_message=self.current_cmd,
            cmd_data=None,
            blocking=True,
            timeout_in_s=timeout,
        )

    def create_instance(self) -> bool:
        """Create DUT auxiliary instance.

        Overridden from base interface in order to use the TX and RX
        tasks, and not duplicate auxiliary method.
        Execute directly the ping-pong to initiate the communication
        with the DUT.

        :return: True if the auxiliary is created and ping-pong
            successful otherwise False

        :raises AuxiliaryCreationError: if instance creation failed
        """
        super().create_instance()
        return self.send_ping_command(timeout=2)

    @flash_target
    @open_connector
    def _create_auxiliary_instance(self) -> bool:
        """Create auxiliary instance flash and connect.

        :return: True if everything was successful otherwise False
        """
        log.internal_info("Auxiliary instance created")
        return True

    @close_connector
    def _delete_auxiliary_instance(self) -> bool:
        """Close the connector communication.

        :return: always True
        """
        log.internal_info("Auxiliary instance deleted")
        return True

    def evaluate_response(self, response: message.Message) -> bool:
        """Evaluate if the received message is knowned and type of
        report.

        .. note:: if a log message type is received just log it

        :param response: reeceived response

        :return: True if the response is a report otherwise False
        """
        if response.get_message_type() == MESSAGE_TYPE.REPORT:
            self.evaluate_report(report_msg=response)
            return True

        if response.get_message_type() == MESSAGE_TYPE.LOG:
            log.internal_info(f"Logging message received from {self.name}: {response}")
            return False

        if response.get_message_type() == MESSAGE_TYPE.ACK:
            log.internal_warning(f"ACK message received from {self.name}: {response}")
            return False

        log.internal_warning(
            f"Message type unknown received from {self.name}: {response}"
        )
        return False

    def evaluate_report(self, report_msg: message.Message) -> None:
        """Evaluate the report type and log the appropriated message.

        :param report_msg: reeceived report message
        """
        if report_msg.get_message_sub_type() == REPORT_TYPE.TEST_FAILED:
            log.error(
                f"Report with verdict FAILED received from {self.name} : {report_msg}"
            )
        elif report_msg.get_message_sub_type() == REPORT_TYPE.TEST_PASS:
            log.internal_info(
                f"Report with verdict PASS received from {self.name} : {report_msg}"
            )

        elif report_msg.get_message_sub_type() == REPORT_TYPE.TEST_NOT_IMPLEMENTED:
            log.internal_warning(
                f"Report with verdict NOT IMPLEMENTED from {self.name} : {report_msg}"
            )
        else:
            log.error(f"Report type unknown received from {self.name} : {report_msg}")

    def wait_and_get_report(
        self, blocking: bool = False, timeout_in_s: int = 0
    ) -> Optional[Message]:
        """Wait for the report coming from the DUT.

        :param blocking: True: wait for timeout to expire, False: return
             immediately
        :param timeout_in_s: if blocking, wait the defined time in
            seconds

        :return: if a report is received return it otherwise None
        """
        try:
            is_report = False
            while not is_report:
                response = self.queue_out.get(blocking, timeout_in_s)
                is_report = self.evaluate_response(response)
            return response
        except queue.Empty:
            return None

    def _run_command(
        self,
        cmd_message: message.Message,
        cmd_data: bytes = None,
    ) -> None:
        """Simply send the given command using the associated channel.

        :param cmd_message: command to send
        :param cmd_data: not use
        """
        try:
            # Serialize and send the message
            self.channel.cc_send(msg=cmd_message.serialize())
        except Exception:
            log.exception(
                f"encountered error while sending message '{cmd_message}' to {self.channel}"
            )

    def _receive_message(self, timeout_in_s: float) -> None:
        """Get message from the device under test.

        :param timeout_in_s: Time in seconds to wait for an answer
        """

        recv_response = self.channel.cc_receive(timeout_in_s)
        response = recv_response.get("msg")

        if response is None:
            return
        elif isinstance(response, str):
            response = response.encode()
        response = Message.parse_packet(response)

        # If a message was received just automatically acknowledge it
        # and populate the queue_out
        if response.msg_type != MESSAGE_TYPE.ACK:
            ack_cmd = response.generate_ack_message(message.MessageAckType.ACK)
            try:
                self.channel.cc_send(msg=ack_cmd.serialize())
            except Exception:
                log.exception(
                    f"encountered error while sending acknowledge message for {response}!"
                )
        self.queue_out.put(response)
