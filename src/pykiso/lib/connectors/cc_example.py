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
import time
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

    def _cc_send(self, msg: bytes) -> None:
        """Sends the message on the channel.

        :param msg: message to send.

        """
        with self.lock:
            log.internal_debug("Send: {}".format(msg))
            # Exit if ack sent
            msg = message.Message.parse_packet(msg)
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

    def _cc_receive(self, timeout: float = 0.1) -> Dict[str, Optional[bytes]]:
        """Craft a Message that would be received from the device under test.

        :param timeout: not use

        :return: dictionary containing the received bytes if successful, otherwise None
        """
        with self.lock:
            received_message = None
            # Simulate a real wait for message
            time.sleep(1e-3)
            if self.last_received_message is not None:
                # Transform into ack
                received_message = message.Message.parse_packet(
                    self.last_received_message
                )
                received_message.msg_type = message.MessageType.ACK
                received_message.sub_type = message.MessageAckType.ACK
                # Delete the stored raw message
                received_message = received_message.serialize()
                self.last_received_message = None
                log.internal_debug("Receive: {}".format(received_message))
            elif self.report_requested_message is not None:
                # Transform message to ACK
                received_message = message.Message.parse_packet(
                    self.report_requested_message
                )
                received_message.msg_type = message.MessageType.REPORT
                received_message.sub_type = message.MessageReportType.TEST_PASS
                # Delete the stored raw message
                received_message = received_message.serialize()
                self.report_requested_message = None
                log.internal_debug("Receive: {}".format(received_message))

            return {"msg": received_message}
