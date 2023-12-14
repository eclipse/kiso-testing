##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Can Auxiliary
*************

:module: can_auxiliary

:synopsis: Auxiliary enables you to read write can messages which are defined in a dbc file.

The goal of this module is to be able to receive and send signals which are defined in dbc file.

.. currentmodule:: can_auxiliary
"""

import logging
import queue
import time
import threading
import functools
from typing import Any, Optional

from pykiso.connector import CChannel
from pykiso.lib.auxiliaries.communication_auxiliary import CommunicationAuxiliary
from pykiso.interfaces.dt_auxiliary import (DTAuxiliaryInterface, open_connector, close_connector)
from pykiso import Message
from pykiso.can_message import CanMessage
from pykiso.can_parser import CanMessageParser
from pykiso.exceptions import AuxiliaryNotStarted

from contextlib import ContextDecorator

log = logging.getLogger(__name__)


class _collect_messages(ContextDecorator):
    """Context manager and decorator for the communication auxiliary
    allowing messages collection (putting them in the queue).
    """

    def __init__(self, com_aux: CommunicationAuxiliary):
        """Constructor used to inherit some of communication auxiliary
        features.
        """
        self.com_aux = com_aux

    def __enter__(self):
        """Set the queue event to allow messages collection."""
        log.internal_debug("Start queueing received messages.")
        self.com_aux.queueing_event.set()

    def __exit__(self, *exc):
        """Clear queue event to stop messages collection."""
        log.internal_debug("Stop queueing received messages.")
        self.com_aux.queueing_event.clear()


class CanAuxiliary(DTAuxiliaryInterface):
    """Auxiliary is used for reading and writing can messages defined in dbc file """

    def __init__(self, com: CChannel, dbc_file: str, **kwargs):
        """Constructor.

        :param com: CChannel that supports raw communication over CAN
        """
        super().__init__(
            is_proxy_capable=True, tx_task_on=True, rx_task_on=True, **kwargs
        )
        self.tx_task_on = False
        self.recv_can_messages = {}
        self.channel = com
        self.queue_tx = queue.Queue()
        self.queueing_event = threading.Event()
        self.collect_messages = functools.partial(_collect_messages, com_aux=self)
        path_to_dbf_file = dbc_file
        self.parser = CanMessageParser(path_to_dbf_file)
        self.can_messages = {}

    @open_connector
    def _create_auxiliary_instance(self) -> bool:
        """Open the connector communication.

        :return: True if the channel is correctly opened otherwise False
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

    def _receive_message(self, timeout_in_s: float = 0.1) -> None:
        """Trigger connector reception method and put received messages
        in the queue.

        :param timeout_in_s: maximum time in second to wait for a response
        """
        try:
            rcv_data = self.channel.cc_receive(timeout=timeout_in_s)
            if rcv_data.get("msg") is not None:
                log.internal_debug(f"received message '{rcv_data}' from {self.channel}")
                message_name = self.parser.dbc.get_message_by_frame_id(rcv_data["remote_id"]).name
                message_signals = self.parser.decode(rcv_data["msg"], rcv_data["remote_id"])
                message_timestamp = float(rcv_data.get("timestamp", 0))
                old_can_message = self.can_messages.get(message_name, None)
                if old_can_message is None:
                    can_msg = CanMessage(message_name, message_signals, message_timestamp)
                    self.can_messages[message_name] = can_msg
                else:
                    self.can_messages[message_name].name = message_name
                    self.can_messages[message_name].signals = message_signals
                    self.can_messages[message_name].time_stamp = message_timestamp
        except (Exception, KeyError):
            log.exception(f"encountered error while receiving message via {self.channel}")
            pass

    def get_last_message(self, message_name: str) -> Optional[CanMessage]:
        """Get the last message which has been received on the bus.
        :param message_name: name of the message, you want to get

        :return: last can massage or return none if the message, or return none if message is not occur 
        """

        return self.can_messages.get(message_name, None)
    

    def get_last_signal(self, message_name: str, signal_name: str) -> Optional[Any]:
        """Get the last message which has been received on the bus.
        :param message_name: name of the message, you want to get

        :return: last can massage or return none if the message or return none if message or signal is not occur
        """

        last_can_message = self.can_messages.get(message_name, None)
        if last_can_message is not None:
            return last_can_message.signals.get(signal_name, None)

    def wait_for_message(
        self,
        message_name: str,
        timeout: float = 0.2
    ) -> dict[str, any]:
        """Get the last message with certain timeout in seconds.
        :param message_name: name of the message to receive
        :param timeout time to wait till a message receives in seconds

        :return: list of last can messages or None if no messages for this component
        """
        last_msg = self.can_messages.get(message_name, None)
        time.sleep(timeout)
        new_can_msg = self.can_messages.get(message_name, None)
        if last_msg is None or last_msg.time_stamp != new_can_msg.time_stamp:
            return new_can_msg
        else:
            return None

    def wait_for_signal(
        self,
        message_name: str,
        expected_signals: dict[str, any],
        timeout: float = 0.2
    ) -> dict[str, any]:
        """Get the last signal of message with certain timeout in seconds.

        :param message_name: name of the message to receive
        :param signal_name: signal name in the message to receive
        :param timeout time to wait till a message receives in seconds

        :return: list of last can messages or None if no messages for this component
        """
        
        t1 = time.perf_counter()
        while time.perf_counter() - t1 < timeout:
            expected_signals_names = expected_signals.keys()
            last_can_msg = self.can_messages.get(message_name, None)
            if last_can_msg is None:
                continue
            for signal_name in expected_signals_names:
                if last_can_msg.signals[signal_name] != expected_signals[signal_name]:
                    continue
            return last_can_msg
        
        return None

    @staticmethod
    def _is_payload_valid(payload: Optional[bytes]) -> bool:
        """Check that the payload is valid. The payload is valid if it is made up of
            8 bytes and bytes 6, 7 and 8 are empty.

        :param payload: payload to check validity

        :return: True if the payload is valid, False if invalid.
        """
        return payload is not None and len(payload) == 8 and (payload[5] == payload[6] == payload[7] == 0)

    def send_message(self, message: str, signals: dict[str, Any]) -> bool:
        """Send one message, the message need to be defined in the dbc file.

        :param message: name of the message to send.
        :param signals: dict of the signals of the message and their value.

        :return: True or False if the message has been successfully send or not.
        """

        for signal, value in signals.items():
            if isinstance(value, str):
                signals[signal] = int.from_bytes(value.encode("utf8"), byteorder="big")
        try:
            message = self.parser.dbc.get_message_by_name(message)
        except KeyError:
            raise ValueError(f"{message} is not a message defined in the DBC file.")
        msg_to_send = self.parser.encode(message, signals)
        self.channel.cc_send(msg_to_send[0], remote_id=msg_to_send[1])

    def run_command(
        self,
        cmd_message: Any,
        cmd_data: Any = None,
        blocking: bool = True,
        timeout_in_s: int = 5,
        timeout_result: Any = None,
    ) -> Any:
        """Send a request by transmitting it through queue_in and
        waiting for a response using queue_out.

        :param cmd_message: command request to the auxiliary
        :param cmd_data: data you would like to populate the command
            with
        :param blocking: If you want the command request to be
            blocking or not
        :param timeout_in_s: Number of time (in s) you want to wait
            for an answer
        :param timeout_result: Value to return when the command times
            out. Defaults to None.

        :raises pykiso.exceptions.AuxiliaryNotStarted: if a command is
            executed although the auxiliary was not started.
        :return: True if the request is correctly executed otherwise
            False
        """
        # avoid a deadlock in case run_command is called within a _receive_message implementation
        # (for e.g. callback implementation) while delete_instance is being executed from the main thread
        if self._stop_event.is_set():
            return timeout_result

        with self.lock:
            if not self.is_instance:
                raise AuxiliaryNotStarted(self.name)

            log.internal_debug(
                f"sending command '{cmd_message}' with payload {cmd_data} using {self.name} aux."
            )
            response_received = timeout_result
            self.queue_in.put((cmd_message, cmd_data))
            try:
                response_received = self.queue_out.get(blocking, timeout_in_s)
                log.internal_debug(
                    f"reply to command '{cmd_message}' received: '{response_received}' in {self.name}"
                )
            except queue.Empty:
                log.error(
                    f"no reply received within time for command {cmd_message} for payload {cmd_data} using {self.name} aux."
                )
        return response_received

    def _run_command(self, cmd_message: str, cmd_data: bytes = None) -> bool:
        """Run the corresponding command.

        :param cmd_message: command type
        :param cmd_data: payload data to send over CChannel

        :return: True if command is executed otherwise False
        """
        if cmd_message == "send":
            try:
                self.channel.cc_send(msg=cmd_data)
            except Exception:
                log.exception(
                    f"encountered error while sending message '{cmd_data}' to {self.channel}"
                )
        elif isinstance(cmd_message, Message):
            log.internal_debug(f"ignored command '{cmd_message} in {self}'")
        else:
            log.internal_warning(f"received unknown command '{cmd_message} in {self}'")