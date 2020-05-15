"""
Communication Channel Via Udp
********************************

:module: cc_udp

:synopsis: Udp communication channel

.. currentmodule:: cc_udp

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

.. warning: Still under test
"""

import socket
from pykiso import connector
from pykiso import message


class CCUdp(connector.CChannel):
    """ UDP implementation of the coordination channel """

    def __init__(self, dest_ip, dest_port, **kwargs):
        # Initialize the super class
        super(CCUdp, self).__init__(**kwargs)
        # Initialize the socket
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Define the max length
        self.max_msg_size = 256

    def _cc_open(self):
        pass

    def _cc_close(self):
        self.udp_socket.close()

    def _cc_send(self, msg, raw=False):
        if raw:
            raise NotImplementedError()
        raw_packet = msg.serialize()
        self.udp_socket.sendto(bytearray(raw_packet), (self.dest_ip, self.dest_port))

    def _cc_receive(self, timeout=0.0000001, raw=False):
        if raw:
            raise NotImplementedError()
        self.udp_socket.settimeout(timeout)

        try:
            read_raw_packet = self.udp_socket.recv(self.max_msg_size)
        except:
            return None
        return message.Message.parse_packet(read_raw_packet)
