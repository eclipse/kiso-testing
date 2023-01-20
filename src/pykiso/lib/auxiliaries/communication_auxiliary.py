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
from __future__ import annotations

import functools
import logging
import queue
import threading
from contextlib import ContextDecorator
from typing import Any, Optional

from pykiso import CChannel, Message
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)

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
        self.queueing_event = threading.Event()
        self.collect_messages = functools.partial(_collect_messages, com_aux=self)

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
            log.internal_debug(
                f"sending command '{cmd_message}' with payload {cmd_data} using {self.name} aux."
            )
            state = None
            self.queue_in.put((cmd_message, cmd_data))
            try:
                state = self.queue_tx.get(blocking, timeout_in_s)
                log.internal_debug(
                    f"command '{cmd_message}' successfully sent for {self.name} aux"
                )
            except queue.Empty:
                log.error(
                    f"no feedback received regarding request {cmd_message} for {self.name} aux."
                )
        return state

    def receive_message(
        self,
        blocking: bool = True,
        timeout_in_s: float = None,
    ) -> Optional[bytes]:
        """Receive a raw message.

        :param blocking: wait for message till timeout elapses?
        :param timeout_in_s: maximum time in second to wait for a response

        :returns: raw message
        """

        # Evaluate if we are in the context manager or not
        in_ctx_manager = False
        if self.queueing_event.is_set():
            in_ctx_manager = True

        log.internal_debug(
            f"retrieving message in {self} (blocking={blocking}, timeout={timeout_in_s})"
        )
        # In case we are not in the context manager, we have a enable the receiver thread (and afterwards disable it)
        if not in_ctx_manager:
            self.queueing_event.set()
        response = self.wait_for_queue_out(blocking=blocking, timeout_in_s=timeout_in_s)
        if not in_ctx_manager:
            self.queueing_event.clear()

        log.internal_debug(f"retrieved message '{response}' in {self}")

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

    def clear_buffer(self) -> None:
        """Clear buffer from old stacked objects"""
        log.internal_info("Clearing buffer. Previous responses will be deleted.")
        with self.queue_out.mutex:
            self.queue_out.queue.clear()

    def _run_command(self, cmd_message: str, cmd_data: bytes = None) -> bool:
        """Run the corresponding command.

        :param cmd_message: command type
        :param cmd_data: payload data to send over CChannel

        :return: True if command is executed otherwise False
        """
        state = False
        if cmd_message == "send":
            try:
                self.channel.cc_send(msg=cmd_data)
                state = True
            except Exception:
                log.exception(
                    f"encountered error while sending message '{cmd_data}' to {self.channel}"
                )
        elif isinstance(cmd_message, Message):
            log.internal_debug(f"ignored command '{cmd_message} in {self}'")
        else:
            log.internal_warning(f"received unknown command '{cmd_message} in {self}'")

        self.queue_tx.put(state)

    def _receive_message(self, timeout_in_s: float) -> None:
        """Get a message from the associated channel. And put the message in
        the queue, if threading event is set.

        :param timeout_in_s: maximum amount of time (seconds) to wait
            for a message
        """
        try:
            rcv_data = self.channel.cc_receive(timeout=timeout_in_s)
            log.internal_debug(f"received message '{rcv_data}' from {self.channel}")
            msg = rcv_data.get("msg")
            if msg is not None and self.queueing_event.is_set():
                self.queue_out.put(rcv_data)
        except Exception:
            log.exception(
                f"encountered error while receiving message via {self.channel}"
            )
