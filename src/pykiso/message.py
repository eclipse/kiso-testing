##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
pykiso Control Message Protocol
*******************************

:module: message

:synopsis: Message that will be send though the different agents

.. currentmodule:: message

"""

from __future__ import annotations

import enum
import itertools
import logging
import struct
from typing import Dict, Optional, Union

msg_cnt = itertools.cycle(
    range(256)
)  # Will be used as token. It increases each time a Message is created

log = logging.getLogger(__name__)


@enum.unique
class MessageType(enum.IntEnum):
    """List of messages allowed."""

    COMMAND = 0
    REPORT = 1
    ACK = 2
    LOG = 3


@enum.unique
class MessageCommandType(enum.IntEnum):
    """List of commands allowed."""

    # Ping
    PING = 0
    # Setups
    TEST_SECTION_SETUP = 1
    TEST_SUITE_SETUP = 2
    TEST_CASE_SETUP = 3
    # Runs
    TEST_SECTION_RUN = 11
    TEST_SUITE_RUN = 12
    TEST_CASE_RUN = 13
    # Teardowns
    TEST_SECTION_TEARDOWN = 21
    TEST_SUITE_TEARDOWN = 22
    TEST_CASE_TEARDOWN = 23
    # Abort
    ABORT = 99


@enum.unique
class MessageReportType(enum.IntEnum):
    """List of possible received messages."""

    TEST_PASS = 0
    TEST_FAILED = 1
    TEST_NOT_IMPLEMENTED = 2

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@enum.unique
class MessageAckType(enum.IntEnum):
    """List of possible received messages."""

    ACK = 0
    NACK = 1


@enum.unique
class TlvKnownTags(enum.IntEnum):
    """List of known / supported tags."""

    TEST_REPORT = 110
    FAILURE_REASON = 112


@enum.unique
class MessageLogType(enum.IntEnum):
    """List of possible received log messages."""

    RESERVED = 0


# Link types and sub-types
type_sub_type_dict = {
    MessageType.COMMAND: MessageCommandType,
    MessageType.REPORT: MessageReportType,
    MessageType.ACK: MessageAckType,
    MessageType.LOG: MessageLogType,
}


class Message:
    """A message who fit testApp protocol.

    The created message is a tlv style message with the following format:
    TYPE: msg_type | message_token | sub_type | errorCode |
    """

    crc_byte_size = 2
    header_size = 8
    max_payload_size = 0xFF
    max_message_size = header_size + max_payload_size + crc_byte_size
    reserved = 0

    def __init__(
        self,
        msg_type: Union[int, MessageType] = 0,
        sub_type: int = 0,
        error_code: int = 0,
        test_suite: int = 0,
        test_case: int = 0,
        tlv_dict: Optional[Dict[str, Union[int, bytes]]] = None,
    ):
        """Create a generic message.

        :param msg_type: Message type
        :type msg_type: MessageType

        :param sub_type: Message sub-type
        :type sub_type: Message<MessageType>Type

        :param error_code: Error value
        :type error_code: integer

        :param test_suite: Suite value
        :type test_suite: integer

        :param test_case: Test value
        :type test_case: integer

        :param tlv_dict: Dictionary containing tlvs elements in the form {'type':'value', ...}
        :type tlv_dict: dict
        """
        self.msg_type = msg_type
        global msg_cnt
        self.msg_token = next(msg_cnt)
        self.sub_type = sub_type
        self.error_code = error_code
        self.test_suite = test_suite
        self.test_case = test_case
        self.tlv_dict = tlv_dict

    def __str__(self):
        """String representation of a message object."""
        string = "msg_type:{}, message_token:{}, type:{}, error_code:{}, reserved:{}, test_suite ID:{}, test_case ID:{}".format(
            self.msg_type,
            self.msg_token,
            self.sub_type,
            self.error_code,
            self.reserved,
            self.test_suite,
            self.test_case,
        )
        if self.tlv_dict is not None:
            # Convert dec to ascii
            tlv = {
                key: "".join(chr(i) for i in val) for key, val in self.tlv_dict.items()
            }
            string += f", tlv_dict:{tlv}"
        return string

    def serialize(self) -> bytes:
        """Serialize message into raw packet.

        Format: | msg_type (1b)     | msg_token (1b)  | sub_type (1b)  | error_code (1b)     |
                | test_section (1b) | test_suite (1b) | test_case (1b) | payload_length (1b) |
                | tlv_type (1b)     | tlv_size (1b)   | ...            | crc_checksum (2b)

        :return: bytes representing the Message object
        """
        raw_packet = b""

        raw_packet += struct.pack(
            "BBBBBBB",
            ((int(self.msg_type) << 4) | (1 << 6)),
            self.msg_token,
            int(self.sub_type),
            self.error_code,
            self.reserved,
            self.test_suite,
            self.test_case,
        )

        # Calculate and convert the dictionaries tlv elements into bytes
        if self.tlv_dict is not None:
            payload = b""
            for key, value in self.tlv_dict.items():
                # Check first if it the dict is conform
                parsed_key = b""
                if isinstance(key, TlvKnownTags):
                    parsed_key = struct.pack("B", int(key))
                else:
                    log.internal_warning("{} is not a supported format".format(key))
                parsed_value = b""
                if isinstance(value, str):  # If string given
                    parsed_value = parsed_value.join(
                        [struct.pack("B", ord(val)) for val in value]
                    )
                elif isinstance(value, int):
                    parsed_value = struct.pack(
                        "H", value
                    )  # TODO check endianness later on
                elif isinstance(value, bytes):
                    parsed_value = value
                else:
                    log.internal_warning("{} is not a supported format".format(value))
                # Add the TLV element:
                payload += parsed_key
                payload += struct.pack("B", len(parsed_value))
                payload += parsed_value
            # Add the tlvs elements within the raw_packet
            raw_packet += struct.pack("B", len(payload))
            raw_packet += payload
        else:
            # Add the payload length to 0
            raw_packet += struct.pack("B", 0)

        # Add crc to raw_packet
        raw_packet += struct.pack("H", self.get_crc(raw_packet, self.crc_byte_size))

        return raw_packet

    @classmethod
    def parse_packet(cls, raw_packet: bytes) -> Message:
        """Factory function to create a Message object from raw data.

        :param raw_packet: array of a received message

        :return: itself
        """
        msg = cls()
        if (not isinstance(raw_packet, bytes)) and (
            len(raw_packet) < (msg.header_size + msg.crc_byte_size)
        ):
            log.error("Packet is not understandable")

        # Check the CRC
        crc = cls.get_crc(raw_packet[: -msg.crc_byte_size], msg.crc_byte_size)
        if crc != struct.unpack("H", raw_packet[-msg.crc_byte_size :])[0]:
            log.error(
                f"CRC check failed {crc} != {struct.unpack('H', raw_packet[-msg.crc_byte_size:])[0]}"
            )

        unpack_header = struct.unpack("BBBBBBB", raw_packet[:7])

        msg.msg_type = (MessageType)(int((unpack_header[0] & 0x30) >> 4))
        msg.msg_token = int(unpack_header[1])
        # Because the sub-type depend on the type:
        msg.sub_type = (type_sub_type_dict[msg.msg_type])(int(unpack_header[2]))
        msg.error_code = int(unpack_header[3])
        msg.reserved = int(unpack_header[4])
        msg.test_suite = int(unpack_header[5])
        msg.test_case = int(unpack_header[6])
        payload_length = int(raw_packet[7])
        # Create payload based on known tlvs
        if payload_length != 0:
            msg.tlv_dict = {}
            for tag, value in cls._parse_tlv(
                raw_packet[msg.header_size : -msg.crc_byte_size]
            ):
                msg.tlv_dict[TlvKnownTags(tag)] = value

        return msg

    @classmethod
    def _parse_tlv(cls, tlv_packet: bytes) -> tuple:
        """Generator used to parse TLV formatted bytes array.

        :param tlv_packet: raw TLV formatted bytes array

        :return: tuple containing the extract tag(int) and value(list)
        """
        tlv_iterator = iter(tlv_packet)
        while True:
            try:
                tag = int(next(itertools.islice(tlv_iterator, 1)))
                length = int(next(itertools.islice(tlv_iterator, 1)))
                value = [val for val in itertools.islice(tlv_iterator, length)]
                yield (tag, value)
            except StopIteration:
                break

    def generate_ack_message(self, ack_type: int) -> Union[Message, None]:
        """Generate acknowledgement to send out.

        :param ack_type: ack or nack

        :return: filled acknowledge message otherwise None
        """
        # Return if wrong parameter given
        if not isinstance(ack_type, MessageAckType):
            return None
        # Create ack message
        ack_message = Message(
            msg_type=MessageType.ACK,
            sub_type=ack_type,
            error_code=0,
            test_suite=self.test_suite,
            test_case=self.test_case,
        )
        ack_message.msg_token = self.msg_token
        # Return the ack message
        return ack_message

    def check_if_ack_message_is_matching(self, ack_message: Message) -> bool:
        """Check if the ack message was for this sent message.

        :param ack_message: received acknowledge message

        :return: True if message type and token are valid otherwise
            False
        """
        if (
            ack_message.msg_type == MessageType.ACK
            and ack_message.msg_token == self.msg_token
        ):
            return True
        else:
            log.internal_info(
                "ack_message: {} \ndifferent of \nthis message: {}".format(
                    str(ack_message), str(self)
                )
            )
            return False

    def get_message_type(self) -> Union[int, MessageType]:
        """Return actual message type."""
        return self.msg_type

    def get_message_token(self) -> int:
        """Return actual message token."""
        return self.msg_token

    def get_message_sub_type(self) -> int:
        """Return actual message subtype."""
        return self.sub_type

    def get_message_tlv_dict(self) -> dict:
        """Return actual message type/length/value dictionary."""
        return self.tlv_dict

    @classmethod
    def get_crc(cls, serialized_msg: bytes, crc_byte_size: int = 2) -> int:
        """Get the CRC checksum for a bytes message.

        :param serialized_msg: message used for the crc calculation
        :param crc_byte_size: number of bytes dedicated for the crc

        :return: CRC checksum
        """

        crc = 0
        crc_mask = 255
        crc_size = (2 ** (crc_byte_size * 8)) - 1

        for _, msg in enumerate(serialized_msg):
            crc = ((crc >> 8) | (crc << 8)) & crc_size
            crc ^= int(msg)
            crc ^= (crc & crc_mask) >> 4
            crc ^= (crc << 12) & crc_size
            crc ^= ((crc & crc_mask) << 5) & crc_size
        return crc
