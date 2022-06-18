##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
CommunicationAuxiliary
**********************

:module: communication_auxiliary

:synopsis: Auxiliary used to send raw bytes via a connector instead of
    pykiso.Messages

.. currentmodule:: communication_auxiliary


"""
import logging
import queue
from typing import Any, Optional

from pykiso import CChannel, DTAuxiliaryInterface, Message

log = logging.getLogger(__name__)


class CommunicationAuxiliary(DTAuxiliaryInterface):
    """Auxiliary used to send raw bytes via a connector instead of pykiso.Messages."""

    def __init__(self, com: CChannel, **kwargs: dict) -> None:
        """Constructor.

        :param com: CChannel that supports raw communication
        """
        super().__init__(
            is_proxy_capable=True, tx_task_on=True, rx_task_on=True, **kwargs
        )
        self.channel = com
        self.queue_tx = queue.Queue()

    def send_message(self, raw_msg: bytes) -> bool:
        """Send a raw message (bytes) via the communication channel.

        :param raw_msg: message to send

        :return: True if command was executed otherwise False
        """
        return self.run_command("send", raw_msg)

    def run_command(
        self,
        cmd_message: Any,
        cmd_data: Any = None,
        blocking: bool = True,
        timeout_in_s: int = None,
    ) -> bool:
        """Send a request by transmitting it through queue_in and
        populate queue_tx with the command verdict (successful or not).

        :param cmd_message: command to send
        :param cmd_data: data you would like to populate the command
            with
        :param blocking: If you want the command request to be
            blocking or not
        :param timeout_in_s: Number of time (in s) you want to wait
            for an answer

        :return: True if the request is correctly executed otherwise
            False
        """
        with self.lock:
            log.debug(
                f"sending command '{cmd_message}' with payload {cmd_data} using {self.name} aux."
            )
            state = None
            self.queue_in.put((cmd_message, cmd_data))
            try:
                state = self.queue_tx.get(blocking, timeout_in_s)
                log.debug(
                    f"command '{cmd_message}' successfully sent for {self.name} aux"
                )
            except queue.Empty:
                log.error(
                    f"no feedback received regarding request {cmd_message} for {self.name} aux."
                )
        return state

    def receive_message(
        self, blocking: bool = True, timeout_in_s: float = None
    ) -> Optional[bytes]:
        """Receive a raw message.

        :param blocking: wait for message till timeout elapses?
        :param timeout_in_s: maximum time in second to wait for a response

        :returns: raw message
        """
        log.debug(
            f"retrieving message in {self} (blocking={blocking}, timeout={timeout_in_s})"
        )
        response = self.wait_for_queue_out(blocking=blocking, timeout_in_s=timeout_in_s)
        log.debug(f"retrieved message '{response}' in {self}")

        # if queue.Empty exception is raised None is returned so just
        # directly return it
        if response is None:
            return None

        msg = response.get("msg")
        remote_id = response.get("remote_id")

        # stay with the old return type to not making a breaking change
        if remote_id is not None:
            return (msg, remote_id)
        return msg

    def _create_auxiliary_instance(self) -> bool:
        """Open the connector communication.

        :return: True if the channel is correctly opened otherwise False
        """
        log.info("Create auxiliary instance")
        log.info("Enable channel")
        try:
            self.channel.open()
            return True
        except Exception:
            log.exception("Unable to open channel communication")
            return False

    def _delete_auxiliary_instance(self) -> bool:
        """Close the connector communication.

        :return: always True
        """
        log.info("Delete auxiliary instance")
        try:
            self.channel.close()
            return True
        except Exception:
            log.exception("Unable to close channel communication")
            return False

    def _run_command(self, cmd_message: str, cmd_data: bytes = None) -> bool:
        """Run the corresponding command.

        :param cmd_message: command type
        :param cmd_data: payload data to send over CChannel

        :return: True if command is executed otherwise False
        """
        state = False
        if cmd_message == "send":
            try:
                self.channel.cc_send(msg=cmd_data, raw=True)
                state = True
            except Exception:
                log.exception(
                    f"encountered error while sending message '{cmd_data}' to {self.channel}"
                )
        elif isinstance(cmd_message, Message):
            log.debug(f"ignored command '{cmd_message} in {self}'")
        else:
            log.warning(f"received unknown command '{cmd_message} in {self}'")

        self.queue_tx.put(state)

    def _receive_message(self, timeout_in_s: float) -> bytes:
        """Get a message from the associated channel.

        :param timeout_in_s: maximum amount of time (seconds) to wait
            for a message

        :return: received message
        """
        try:
            rcv_data = self.channel.cc_receive(timeout=timeout_in_s, raw=True)
            msg = rcv_data.get("msg")
            if msg is not None:
                log.debug(f"received message '{rcv_data}' from {self.channel}")
                self.queue_out.put(rcv_data)
        except Exception:
            log.exception(
                f"encountered error while receiving message via {self.channel}"
            )
