"""
Virtual Communication channel for tests
****************************************

:module: cc_example

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

.. warning: Still under test
"""

import logging

from pykiso import connector
from pykiso import message


class CCExample(connector.CChannel):
    def __init__(self, name=None, **kwargs):
        super(CCExample, self).__init__(name=name)
        # Private attribute
        self.options = kwargs
        self.last_received_message = None
        self.report_requested_message = None

    def _cc_open(self):
        """ Open the channel """
        logging.info("open channel")

    def _cc_close(self):
        """ Close the channel """
        logging.info("close channel")

    def _cc_send(self, msg, raw=False):
        """ Sends the message on the channel """
        if raw:
            raise NotImplementedError()
        logging.info("Send: {}".format(msg))
        # Exit if ack sent
        if msg.get_message_type() == message.MessageType.ACK:
            return

        # Else save received message
        self.last_received_message = msg.serialize()
        # Check if it is a run test-case message and save it for the report
        if msg.sub_type == message.MessageCommandType.TEST_CASE_RUN:
            self.report_requested_message = msg.serialize()

    def _cc_receive(self, timeout, raw=False):
        """ Reads from the channel - decorator usage for test"""
        if raw:
            raise NotImplementedError()
        # logging.info("Read in: {}".format(self))
        if self.last_received_message != None:
            # Transform into ack
            r_message = message.Message.parse_packet(self.last_received_message)
            r_message.msg_type = message.MessageType.ACK
            r_message.sub_type = message.MessageAckType.ACK
            # Delete the stored raw message
            self.last_received_message = None
            # Return the ACK
            logging.info("Receive: {}".format(r_message))
            return r_message
        elif self.report_requested_message != None:
            # Transform message to ACK
            r_message = message.Message.parse_packet(self.report_requested_message)
            r_message.msg_type = message.MessageType.REPORT
            r_message.sub_type = message.MessageReportType.TEST_PASS
            # Delete the stored raw message
            self.report_requested_message = None
            # Return REPORT
            logging.info("Receive: {}".format(r_message))
            return r_message
