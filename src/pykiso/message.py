"""
pykiso Control Message Protocol
*******************************

:module: message

:synopsis: Message that will be send though the different agents

.. currentmodule:: message

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0
"""

from __future__ import annotations
import enum
import logging
import struct
import itertools


message_counter = 0  # Will be used as token


@enum.unique
class MessageType(enum.IntEnum):
    """ List of messages allowed
    """

    COMMAND = 0
    REPORT = 1
    ACK = 2
    LOG = 3


@enum.unique
class MessageCommandType(enum.IntEnum):
    """ List of commands allowed
    """

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
    """ List of possible recieved messages
    """

    TEST_PASS = 0
    TEST_FAILED = 1


@enum.unique
class MessageAckType(enum.IntEnum):
    """ List of possible recieved messages
    """

    ACK = 0
    NACK = 1


@enum.unique
class TlvKnownTags(enum.IntEnum):
    """ List of known / supported tags
    """

    TEST_REPORT = 110
    FAILURE_REASON = 112


# Link types and sub-types
type_sub_type_dict = {
    MessageType.COMMAND: MessageCommandType,
    MessageType.REPORT: MessageReportType,
    MessageType.ACK: MessageAckType,
    MessageType.LOG: 0,
}


class Message:
    """ A message

    The created message is a tlv style message with the following format:
    TYPE: msg_type | message_token | sub_type | errorCode |

    :raise:
        * The message-type and sub-type are linked. a wrong combination can rais an error

    """

    def __init__(
        self,
        msg_type: MessageType = 0,
        sub_type=0,
        error_code: int = 0,
        test_suite: int = 0,
        test_case: int = 0,
        tlv_dict=None,
    ):
        """ Create a generic message

        :param msg_type: Message type
        :type msg_type: MessageType

        :param sub_type: Message sub-type
        :type sub_type: Message<MessageType>Type

        :param error_code: Error value
        :type error_code: integer

        :param test_section: Section value
        :type test_section: integer

        :param test_suite: Suite value
        :type test_suite: integer

        :param test_case: Test value
        :type test_case: integer

        :param tlv_dict: Dictionary containing tlvs elements in the form {'type':'value', ...}
        :type tlv_dict: dict
        """
        self.msg_type = msg_type
        global message_counter
        self.msg_token = (message_counter + 1) % 256
        message_counter += 1
        self.sub_type = sub_type
        self.error_code = error_code
        self.reserved = 0
        self.test_suite = test_suite
        self.test_case = test_case
        self.tlv_dict = tlv_dict

    def __str__(self):
        """ String representation of a message object
        """
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
            string += ", tlv_dict:{}".format(self.tlv_dict)
        return string

    def serialize(self) -> bytes:
        """ Serialize message into raw packet

        Format: | msg_type (1b)     | msg_token (1b)  | sub_type (1b)  | error_code (1b)     |
                | test_section (1b) | test_suite (1b) | test_case (1b) | payload_length (1b) |
                | tlv_type (1b)     | tlv_size (1b)   | ...

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
                    logging.warning("{} is not a supported format".format(key))
                parsed_value = b""
                if isinstance(value, str):  # If string given
                    parsed_value = parsed_value.join(
                        [struct.pack("B", ord(val)) for val in value]
                    )
                elif isinstance(value, int):
                    parsed_value = struct.pack(
                        "H", value
                    )  # TODO check endianess later on
                elif isinstance(value, bytes):
                    parsed_value = value
                else:
                    logging.warning("{} is not a supported format".format(value))
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
        return raw_packet

    @classmethod
    def parse_packet(cls, raw_packet: bytes) -> Message:
        """ factory function to create a Message object from raw data

        :param raw_packet: array of a received message

        :return: itself
        """
        msg = cls()

        if not isinstance(raw_packet, bytes) and len(raw_packet) < 8:
            logging.error("Packet is not understandable")

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
            for tag, value in cls._parse_tlv(raw_packet[8:]):
                msg.tlv_dict[TlvKnownTags(tag)] = value

        return msg

    @classmethod
    def _parse_tlv(cls, tlv_packet):
        """Generator used to parse TLV formated bytes array.
        :param tlv_packet: raw TLV formated bytes array
        :type tlv_packet: bytes

        :return: tuple conatining the extract tag(int) and value(list)
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

    def generate_ack_message(self, ack_type):
        """ Generate acknowledgement to send out

        :param ack_type: ack or nack
        :type ack_type: MessageAckType
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

    def check_if_ack_message_is_matching(self, ack_message):
        """ Check if the ack message was for this sent message
        """
        if (
            ack_message.msg_type == MessageType.ACK
            and ack_message.msg_token == self.msg_token
        ):
            return True
        else:
            logging.info(
                "ack_message: {} \ndifferent of \nthis message: {}".format(
                    str(ack_message), str(self)
                )
            )
            return False

    def get_message_type(self):
        return self.msg_type

    def get_message_token(self):
        return self.msg_token

    def get_message_sub_type(self):
        return self.sub_type

    def get_message_tlv_dict(self):
        return self.tlv_dict
