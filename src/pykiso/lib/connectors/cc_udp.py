##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via Udp
********************************

:module: cc_udp

:synopsis: Udp communication channel

.. currentmodule:: cc_udp


.. warning: Still under test
"""

import logging
import socket
from typing import Dict, Optional

from pykiso import connector

log = logging.getLogger(__name__)


class CCUdp(connector.CChannel):
    """UDP implementation of the coordination channel."""

    def __init__(self, dest_ip: str, dest_port: int, **kwargs):
        """Initialize attributes.

        :param dest_ip: destination ip address
        :param dest_port: destination port
        """
        # Initialize the super class
        super().__init__(**kwargs)
        # Initialize the socket
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.udp_socket = None
        self.source_addr = None
        # Define the max length
        self.max_msg_size = 256
        # Set a timeout to send the signal to the GIL to change thread.
        # In case of a multi-threading system, all tasks will be called one after the other.
        self.timeout = 1e-6

    def _cc_open(self) -> None:
        """Open the udp socket."""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _cc_close(self) -> None:
        """Close the udp socket."""
        self.udp_socket.close()

    def _cc_send(self, msg: bytes) -> None:
        """Send message using udp socket

        :param msg: message to send, should bytes.
        """

        self.udp_socket.sendto(msg, (self.dest_ip, self.dest_port))

    def _cc_receive(self, timeout: float = 0.0000001) -> Dict[str, Optional[bytes]]:
        """Read message from socket.

        :param timeout: timeout applied on receive event

        :return: dictionary containing the received bytes if successful, otherwise None
        """
        self.udp_socket.settimeout(timeout or self.timeout)

        try:
            msg_received, self.source_addr = self.udp_socket.recvfrom(self.max_msg_size)

        # catch the errors linked to the socket timeout without blocking
        except BlockingIOError:
            log.internal_debug(f"encountered error while receiving message via {self}")
            return {"msg": None}
        except socket.timeout:
            log.internal_debug(f"encountered error while receiving message via {self}")
            return {"msg": None}
        except BaseException:
            log.exception(f"encountered error while receiving message via {self}")
            return {"msg": None}

        return {"msg": msg_received}
