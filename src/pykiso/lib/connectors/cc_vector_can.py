##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
CAN Communication Channel using Vector hardware
***********************************************

:module: cc_vector_can

:synopsis: CChannel implementation for CAN(fd) using Vector API from python-can

.. currentmodule:: cc_vector_can

"""

import logging
from typing import Dict, Optional, Union

import can
import can.bus
import can.interfaces.vector
from can.interfaces.vector.canlib import get_channel_configs

from pykiso import CChannel, Message

MessageType = Union[Message, bytes]

log = logging.getLogger(__name__)


class CCVectorCan(CChannel):
    """CAN FD channel-adapter."""

    def __init__(
        self,
        bustype: str = "vector",
        poll_interval: float = 0.01,
        rx_queue_size: int = 524288,
        serial: int = None,
        channel: int = 3,
        bitrate: int = 500000,
        data_bitrate: int = 2000000,
        fd: bool = True,
        enable_brs: bool = False,
        app_name: str = None,
        can_filters: list = None,
        is_extended_id: bool = False,
        **kwargs,
    ):
        """Initialize can channel settings.

        :param bustype: python-can interface modules used
        :param poll_interval: Poll interval in seconds.
        :param rx_queue_size: Number of messages in receive queue
        :param serial: Vector Box's serial number. Can be replaced by the
            "AUTO" flag to trigger the Vector Box automatic detection.
        :param channel: The channel indexes to create this bus with
        :param bitrate: Bitrate in bits/s.
        :param app_name: Name of application in Hardware Config.
            If set to None, the channel should be a global channel index.
        :param data_bitrate: Which bitrate to use for data phase in CAN FD.
        :param fd: If CAN-FD frames should be supported.
        :param enable_brs: sets the bitrate_switch flag to use higher transmission speed
        :param can_filters: A iterable of dictionaries each containing
            a “can_id”, a “can_mask”, and an optional “extended” key.
        :param is_extended_id: This flag controls the size of the arbitration_id field.

        """
        super().__init__(**kwargs)
        self.bustype = bustype
        self.poll_interval = poll_interval
        self.rx_queue_size = rx_queue_size
        if str(serial).upper() == "AUTO":
            self.serial = detect_serial_number()
        else:
            self.serial = serial if not isinstance(serial, str) else int(serial)
        self.channel = channel
        self.app_name = app_name
        self.bitrate = bitrate
        self.data_bitrate = data_bitrate
        self.is_extended_id = is_extended_id
        self.fd = fd
        self.enable_brs = enable_brs
        self.can_filters = can_filters
        self.remote_id = None
        self.bus = None
        # Set a timeout to send the signal to the GIL to change thread.
        # In case of a multi-threading system, all tasks will be called one after the other.
        self.timeout = 1e-6

        if self.enable_brs and not self.fd:
            log.internal_warning(
                "Bitrate switch will have no effect because option is_fd is set to false."
            )

    def _cc_open(self) -> None:
        """Open a can bus channel and set filters for reception."""
        log.internal_info(f"CAN bus channel open: {self.channel}")
        self.bus = can.interface.Bus(
            bustype=self.bustype,
            poll_interval=self.poll_interval,
            rx_queue_size=self.rx_queue_size,
            serial=self.serial,
            app_name=self.app_name,
            channel=self.channel,
            bitrate=self.bitrate,
            data_bitrate=self.data_bitrate,
            fd=self.fd,
            bitrate_switch=self.enable_brs,
            can_filters=self.can_filters,
        )

    def _cc_close(self) -> None:
        """Close the current can bus channel."""
        log.internal_info(f"CAN bus channel closed: {self.channel}")
        self.bus.shutdown()
        self.bus = None

    def _cc_send(self, msg, remote_id: Optional[int] = None, **kwargs) -> None:
        """Send a CAN message at the configured id.

        If remote_id parameter is not given take configured ones.

        :param msg: data to send
        :param remote_id: destination can id used
        :param kwargs: named arguments

        """
        remote_id = remote_id or self.remote_id

        can_msg = can.Message(
            arbitration_id=remote_id,
            data=msg,
            is_extended_id=self.is_extended_id,
            is_fd=self.fd,
            bitrate_switch=self.enable_brs,
        )
        self.bus.send(can_msg)

        log.internal_debug(f"sent CAN Message: {can_msg}")

    def _cc_receive(self, timeout=0.0001) -> Dict[str, Union[MessageType, int]]:
        """Receive a can message using configured filters.

        :param timeout: timeout applied on reception

        :return: the received data and the source can id
        """
        try:  # Catch bus errors & rcv.data errors when no messages where received
            received_msg = self.bus.recv(timeout=timeout or self.timeout)

            if received_msg is not None:
                frame_id = received_msg.arbitration_id
                payload = received_msg.data
                log.internal_debug(f"received CAN Message: {frame_id}, {payload}")

                return {"msg": payload, "remote_id": frame_id}
            else:
                return {"msg": None}
        except BaseException:
            log.exception(f"encountered error while receiving message via {self}")
            return {"msg": None}


def detect_serial_number() -> int:
    """Provide the serial number of the currently available Vector Box to be used.

    If several Vector Boxes are detected, the one with the lowest serial number is selected.
    If no Vector Box is connected, a ConnectionRefused error is thrown.

    :return: the Vector Box serial number
    :raises ConnectionRefusedError: raised if no Vector box is currently available
    """
    # Get all channels configuration
    channel_configs = get_channel_configs()
    # Getting all serial numbers
    serial_numbers = set()
    for channel_config in channel_configs:
        serial_number = channel_config.serial_number
        if serial_number != 0:
            serial_numbers.add(channel_config.serial_number)
    if serial_numbers:
        # if several devices are discovered, the first Vector Box is chosen
        serial_number = min(serial_numbers)
        log.internal_info(f"Using Vector Box with serial number {serial_number}")
        return serial_number
    else:
        raise ConnectionRefusedError("No Vector box is currently available")
