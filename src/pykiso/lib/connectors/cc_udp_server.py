##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel via UDP server
************************************

:module: cc_udp_server

:synopsis: basic UDP server

.. currentmodule:: cc_udp_server

.. warning:: if multiple clients are connected to this server,
    ensure that each client receives all necessary responses before
    receiving messages again. Otherwise the responses may be
    sent to the wrong client

"""
import logging
import socket
from typing import Dict, Optional, Union

from pykiso import Message, connector

log = logging.getLogger(__name__)


class CCUdpServer(connector.CChannel):
    """Connector channel used to set up an UDP server."""

    def __init__(self, dest_ip: str, dest_port: int, **kwargs):
        """Initialize attributes.

        :param dest_ip: destination port
        :param dest_port: destination port
        """
        super().__init__(**kwargs)
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = None
        self.max_msg_size = 256
        # Set a timeout to send the signal to the GIL to change thread.
        # In case of a multi-threading system, all tasks will be called one after the other.
        self.timeout = 1e-6

    def _cc_open(self) -> None:
        """Bind UDP socket with configured port and IP address."""
        log.internal_info(f"UDP socket open at address: {self.address}")
        self.udp_socket.bind((self.dest_ip, self.dest_port))

    def _cc_close(self) -> None:
        """Close UDP socket."""
        log.internal_info(f"UDP socket closed at address: {self.address}")
        self.udp_socket.close()

    def _cc_send(self, msg: bytes) -> None:
        """Send back a UDP message to the previous sender.

        :param msg: message to sent, should be bytes
        """
        log.internal_debug(f"UDP server send: {msg} at {self.address}")
        self.udp_socket.sendto(msg, self.address)

    def _cc_receive(self, timeout=0.0000001) -> Dict[str, Optional[bytes]]:
        """Read message from UDP socket.

        :param timeout: timeout applied on receive event

        :return: Message if successful, otherwise none
        """

        self.udp_socket.settimeout(timeout or self.timeout)

        try:
            msg_received, self.address = self.udp_socket.recvfrom(self.max_msg_size)
            log.internal_debug(f"UDP server receives: {msg_received} at {self.address}")
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
