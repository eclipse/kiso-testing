##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Virtual Communication Channel for tests
***************************************

:module: cc_example


.. warning: Still under test
"""

import logging
import threading
from typing import Dict, Optional

from pykiso import connector, message

log = logging.getLogger(__name__)


class CCExample(connector.CChannel):
    """Only use for development purpose.

    This channel simply handle basic TestApp response mechanism.
    """

    def __init__(self, name: Optional[str] = None, **kwargs):
        """Initialize attributes.

        :param name: name of the communication channel
        """
        super().__init__(name=name)
        self.options = kwargs
        self.last_received_message = None
        self.report_requested_message = None
        self.lock = threading.Lock()

    def _cc_open(self) -> None:
        """Open the channel."""
        log.internal_info("open channel")

    def _cc_close(self) -> None:
        """Close the channel."""
        log.internal_info("close channel")

    def _cc_send(self, msg: message.Message, raw: bool = False) -> None:
        """Sends the message on the channel.

        :param msg: message to send, should be Message type like.
        :param raw: if raw is false serialize it using Message serialize.

        :raise NotImplementedError: sending raw bytes is not supported.
        """
        with self.lock:
            if raw:
                raise NotImplementedError()
            log.internal_debug("Send: {}".format(msg))
            # Exit if ack sent
            if msg.get_message_type() == message.MessageType.ACK:
                return

            # Else save received message
            self.last_received_message = msg.serialize()

            # Check if it is a run test-case message and save it for the report
            if (
                msg.sub_type in set(message.MessageCommandType)
                and msg.sub_type != message.MessageCommandType.PING
                and msg.sub_type != message.MessageCommandType.ABORT
            ):

                self.report_requested_message = msg.serialize()

    def _cc_receive(
        self, timeout: float = 0.1, raw: bool = False
    ) -> Dict[str, Optional[message.Message]]:
        """Reads from the channel - decorator usage for test.

        :param timeout: not use
        :param raw: if raw is false serialize it using Message serialize.

        :raise NotImplementedError: receiving raw bytes is not supported.

        :return: Message if successful, otherwise None
        """
        with self.lock:
            if raw:
                raise NotImplementedError()
            if self.last_received_message is not None:
                # Transform into ack
                r_message = message.Message.parse_packet(self.last_received_message)
                r_message.msg_type = message.MessageType.ACK
                r_message.sub_type = message.MessageAckType.ACK
                # Delete the stored raw message
                self.last_received_message = None
                # Return the ACK
                log.internal_debug("Receive: {}".format(r_message))
                return {"msg": r_message}
            elif self.report_requested_message is not None:
                # Transform message to ACK
                r_message = message.Message.parse_packet(self.report_requested_message)
                r_message.msg_type = message.MessageType.REPORT
                r_message.sub_type = message.MessageReportType.TEST_PASS
                # Delete the stored raw message
                self.report_requested_message = None
                # Return REPORT
                log.internal_debug("Receive: {}".format(r_message))
                return {"msg": r_message}
            else:
                return {"msg": None}
