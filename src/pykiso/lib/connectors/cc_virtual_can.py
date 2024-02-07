##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Virtual Can Communication Channel
*********************************

:module: cc_virtual_can

:synopsis: CChannel implementation for victual CAN using UDP multicast API from python-can

.. currentmodule:: cc_virtual_can

"""
import logging
from typing import Dict, Optional, Union

from pykiso import connector

try:
    import can
    from can.interfaces.udp_multicast.bus import UdpMulticastBus
except ImportError as e:
    raise ImportError(f"{e.name} dependency missing, consider installing pykiso with 'pip install pykiso[can]'")

log = logging.getLogger(__name__)


class CCVirtualCan(connector.CChannel):
    def __init__(
        self,
        channel: UdpMulticastBus = UdpMulticastBus.DEFAULT_GROUP_IPv4,
        receive_own_messages: bool = False,
        is_fd: bool = True,
        enable_brs: bool = False,
        is_extended_id: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.channel = channel
        self.interface = "udp_multicast"
        self.receive_own_messages = receive_own_messages
        self.is_fd = is_fd
        self.enable_brs = enable_brs
        self.is_extended_id = is_extended_id
        self._is_open = False
        self.timeout = 1e-6
        self.config = {
            "interface": self.interface,
            "channel": self.channel,
            "preserve_timestamps": False,
            "receive_own_messages": self.receive_own_messages,
            "fd": self.is_fd,
        }

    @property
    def is_open(self):
        return self._is_open

    def _cc_open(self) -> None:
        """Open a can bus channel."""
        if self.is_open:
            log.info(f"{self} is already open")
            return
        self.bus = can.Bus(**self.config)
        self._is_open = True

    def _cc_close(self) -> None:
        """Close the current can bus channel."""
        self.bus.shutdown()
        self.bus = None
        self._is_open = False

    def _cc_send(self, msg: bytes, remote_id: Optional[int] = None, **kwargs) -> None:
        """Send a CAN message at the configured id.

        If remote_id parameter is not given take configured ones

        :param msg: data to send
        :param remote_id: destination can id used
        :param kwargs: named arguments
        """

        remote_id = remote_id or self.remote_id

        can_msg = can.Message(
            arbitration_id=remote_id,
            data=msg,
            is_fd=self.is_fd,
            dlc=len(msg),
            is_extended_id=self.is_extended_id,
            bitrate_switch=self.enable_brs,
            check=True,
        )
        self.bus.send(can_msg)

        log.internal_debug("%s sent CAN Message: %s, data: %s", self, can_msg, msg)

    def _cc_receive(self, timeout: float = 0.0001) -> Dict[str, Union[bytes, int, None]]:
        """Receive a can message using configured filters.

        :param timeout: timeout applied on reception

        :return: the received data and the source can id
        """
        try:
            received_msg = self.bus.recv(timeout=timeout or self.timeout)

            if received_msg is not None:
                frame_id = received_msg.arbitration_id
                payload = received_msg.data
                timestamp = received_msg.timestamp

                log.internal_debug(
                    "received CAN Message: %s, %s, %s",
                    frame_id,
                    payload,
                    timestamp,
                )
                return {
                    "msg": payload,
                    "remote_id": frame_id,
                    "timestamp": timestamp,
                }
            else:
                return {"msg": None}
        except can.CanError as can_error:
            log.internal_info("encountered CAN error while receiving message: %s", can_error)
            return {"msg": None}
        except Exception:
            log.exception(f"encountered error while receiving message via {self}")
            return {"msg": None}
