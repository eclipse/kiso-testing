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
from typing import Optional

from pykiso import AuxiliaryInterface, CChannel, Message

log = logging.getLogger(__name__)


class CommunicationAuxiliary(AuxiliaryInterface):
    """Auxiliary used to send raw bytes via a connector instead of pykiso.Messages."""

    def __init__(self, com: CChannel, **kwargs):
        """Constructor.

        :param com: CChannel that supports raw communication
        """
        super().__init__(is_proxy_capable=True, **kwargs)
        self.channel = com

    def send_message(self, raw_msg: bytes) -> bool:
        """Send a raw message (bytes) via the communication channel.

        :param raw_msg: message to send

        :return: True if command was executed otherwise False
        """
        return self.run_command("send", raw_msg, timeout_in_s=None)

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
        response = self.wait_and_get_report(
            blocking=blocking, timeout_in_s=timeout_in_s
        )
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

        :return: always True
        """
        state = False
        log.info("Create auxiliary instance")
        log.info("Enable channel")
        try:
            self.channel.open()
            state = True
        except Exception:
            log.exception("Unable to open channel communication")
            self.stop()
        return state

    def _delete_auxiliary_instance(self) -> bool:
        """Close the connector communication.

        :return: always True
        """
        log.info("Delete auxiliary instance")
        try:
            self.channel.close()
        except Exception:
            log.exception("Unable to close channel communication")
        return True

    def _run_command(self, cmd_message: bytes, cmd_data: bytes = None) -> bool:
        """Run the corresponding command.

        :param cmd_message: command type
        :param cmd_data: payload data to send over CChannel

        :return: True if command is executed otherwise False
        """
        if cmd_message == "send":
            try:
                self.channel.cc_send(msg=cmd_data, raw=True)
                return True
            except Exception:
                log.exception(
                    f"encountered error while sending message '{cmd_data}' to {self.channel}"
                )
        elif isinstance(cmd_message, Message):
            log.debug(f"ignored command '{cmd_message} in {self}'")
            return True
        else:
            log.warning(f"received unknown command '{cmd_message} in {self}'")
        return False

    def _abort_command(self) -> None:
        """No-op since we don't wait for ACKs"""
        pass

    def _receive_message(self, timeout_in_s: float) -> bytes:
        """No-op since it's handled in _run_command

        :param timeout_in_s: not used

        :return: received message
        """
        try:
            rcv_data = self.channel.cc_receive(timeout=0, raw=True)
            msg = rcv_data.get("msg")
            if msg is not None:
                log.debug(f"received message '{rcv_data}' from {self.channel}")
                return rcv_data
        except Exception:
            log.exception(
                f"encountered error while receiving message via {self.channel}"
            )
            return None
