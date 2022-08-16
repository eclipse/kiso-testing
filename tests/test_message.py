##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import itertools
import struct
import unittest

import pytest

from pykiso import message as message_mod
from pykiso.message import (
    Message,
    MessageAckType,
    MessageCommandType,
    MessageType,
    TlvKnownTags,
)


class MessageTest(unittest.TestCase):
    def test_message_creation(self):
        msg = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        assert msg.test_suite == 2
        assert msg.test_case == 3
        assert msg.msg_type == MessageType.COMMAND

    def test_message_consistency_with_tlv_dict(self):
        # Create the message
        tlv_dict_to_send = {
            TlvKnownTags.TEST_REPORT: "OK",
            TlvKnownTags.FAILURE_REASON: b"\x12\x34\x56",
        }
        message_for_test = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
            tlv_dict=tlv_dict_to_send,
        )
        # Check message content
        assert MessageType.COMMAND == message_for_test.get_message_type()
        assert (
            MessageCommandType.TEST_CASE_SETUP
            == message_for_test.get_message_sub_type()
        )

        assert next(message_mod.msg_cnt) - 1 == message_for_test.get_message_token()
        assert tlv_dict_to_send == message_for_test.get_message_tlv_dict()

    def test_message_serialization_no_tlv(self):
        # Create the message
        message_for_test = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        # Check serialization output
        output_result = message_for_test.serialize()
        # Remove the crc (not the purpose of this test)
        output_result = output_result[:-2]

        expected_output = "40{:02x}030000020300".format(next(message_mod.msg_cnt) - 1)

        assert expected_output == output_result.hex()

    def test_message_serialization_with_tlv(self):
        # Create the message
        tlv_dict_to_send = {
            TlvKnownTags.TEST_REPORT: "OK",
            TlvKnownTags.FAILURE_REASON: b"\x12\x34\x56",
        }
        message_mod.msg_cnt = itertools.cycle(range(256))
        message_for_test = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
            tlv_dict=tlv_dict_to_send,
        )
        # Check serialization output
        output_result = message_for_test.serialize()
        expected_output = (
            "40{:02x}0300000203".format(next(message_mod.msg_cnt) - 1)
            + "09"
            + "6e"
            + "02"
            + "4f4b"
            + "70"
            + "03"
            + "123456"
        )
        # Remove the crc (not the purpose of this test)
        output_result = output_result[:-2]
        assert expected_output == output_result.hex()

    def test_parse_back_message_with_no_tlv(self):
        # Create raw message
        raw_message = b"\x40\x01\x03\x00\x01\x02\x03\x00"
        # Parse message back
        message = Message.parse_packet(raw_message)
        # Check content
        assert MessageType.COMMAND == message.get_message_type()
        assert MessageCommandType.TEST_CASE_SETUP == message.get_message_sub_type()
        assert 1 == message.get_message_token()
        assert None == message.get_message_tlv_dict()

    def test_parse_back_message_with_tlv(self):
        # Create raw message
        raw_message = b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56\x00\x8f"
        # Parse message back
        message = Message.parse_packet(raw_message)
        # Check content
        assert MessageType.COMMAND == message.get_message_type()
        assert MessageCommandType.TEST_CASE_SETUP == message.get_message_sub_type()
        assert 1 == message.get_message_token()
        assert {
            TlvKnownTags.TEST_REPORT: [79, 75],
            TlvKnownTags.FAILURE_REASON: [18, 52, 86],
        } == message.get_message_tlv_dict()

    def test_ack_message_matching(self):
        # Create the messages
        message_sent = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        raw_ack_message_received = struct.pack(
            "BBBBBBBB", 0x60, message_sent.msg_token, 0x00, 0x00, 0x01, 0x02, 0x03, 0x00
        )
        # Parse and compare
        message_received = Message.parse_packet(raw_ack_message_received)
        assert message_sent.check_if_ack_message_is_matching(message_received) is True

    def test_ack_message_not_matching(self):
        message_sent = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )

        message_rcv = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )

        assert message_sent.check_if_ack_message_is_matching(message_rcv) is False

    def test_ack_message_gen_and_match(self):
        # Create the messages
        message_sent = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        ack_message_received = message_sent.generate_ack_message(MessageAckType.ACK)
        # Parse and compare
        assert (
            message_sent.check_if_ack_message_is_matching(ack_message_received) is True
        )

    def test_ack_message_gen_and_match_wrong_type(self):
        # Create the messages
        message_sent = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        ack_message_received = message_sent.generate_ack_message(
            TlvKnownTags.TEST_REPORT
        )
        # Parse and compare
        self.assertIsNone(ack_message_received)

    def test_get_crc(self):
        crc = Message.get_crc(b"@\x01\x00\x00\x00UU\x00", 2)
        assert b"\xc5\n" == struct.pack("H", crc)

    def test_generate_ack_message_wrong_type(self):
        msg = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )

        assert msg.generate_ack_message(1) is None
