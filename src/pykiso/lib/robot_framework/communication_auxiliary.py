##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication auxiliary plugin
******************************

:module: communication_auxiliary

:synopsis: implementation of existing CommunicationAuxiliary for Robot
    framework usage.

.. currentmodule:: communication_auxiliary

"""
import threading
from typing import Tuple, Union

from robot.api import logger
from robot.api.deco import keyword, library

from ..auxiliaries.communication_auxiliary import (
    CommunicationAuxiliary as ComAux,
)
from .aux_interface import RobotAuxInterface


@library(version="0.1.0")
class CommunicationAuxiliary(RobotAuxInterface):
    """Robot framework plugin for CommunicationAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=ComAux)
        self.queueing_event = threading.Event()

    @keyword(name="Send message")
    def send_message(
        self,
        raw_msg: bytes,
        aux_alias: str,
    ) -> bool:
        """Send a raw message via the communication channel.

        :param aux_alias: auxiliary's alias
        :param raw_msg: message to send

        :return: state representing the send message command completion
        """

        aux = self._get_aux(aux_alias)
        state = aux.send_message(raw_msg)
        logger.info(f"send message {raw_msg} using {aux_alias}")
        return state

    @keyword(name="Start Recording Received Messages")
    def start_recording_received_messages(self) -> None:
        """Start recording received com_aux messages"""

        self.queueing_event.set()

    @keyword(name="Stop Recording Received Messages")
    def stop_recording_received_messages(self) -> None:
        """Stop recording received com_aux messages"""

        self.queueing_event.clear()

    @keyword(name="Clear Buffer")
    def clear_buffer(self, aux_alias: str) -> None:
        """Clear buffer from old stacked objects"""

        aux = self._get_aux(aux_alias)
        aux.clear_buffer()

    @keyword(name="Receive message")
    def receive_message(
        self,
        aux_alias: str,
        blocking: bool = True,
        timeout_in_s: float = None,
    ) -> Union[list, Tuple[list, int]]:
        """Return a raw received message from the queue.

        :param aux_alias: auxiliary's alias
        :param blocking: wait for message till timeout elapses?
        :param timeout_in_s: maximum time in second to wait for a
            response

        :returns: raw message and source (return type could be different
            depending on the associated channel)
        """

        aux = self._get_aux(aux_alias)
        source = None
        msg = []
        recv_msg = aux.receive_message(blocking, timeout_in_s)
        try:
            if recv_msg is not None:
                msg, source = recv_msg
        except ValueError:
            msg = recv_msg
        logger.info(f"message received {msg} on {aux_alias}")
        return list(msg), source
