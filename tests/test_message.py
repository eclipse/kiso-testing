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
        message_for_test = Message(
            msg_type=MessageType.COMMAND,
            sub_type=MessageCommandType.TEST_CASE_SETUP,
            test_suite=2,
            test_case=3,
        )
        print(message_for_test)  # Not best unittest -> Used to compare with old code

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
        self.assertEqual(MessageType.COMMAND, message_for_test.get_message_type())
        self.assertEqual(
            MessageCommandType.TEST_CASE_SETUP, message_for_test.get_message_sub_type()
        )
        self.assertEqual(
            next(message_mod.msg_cnt) - 1, message_for_test.get_message_token()
        )
        self.assertDictEqual(tlv_dict_to_send, message_for_test.get_message_tlv_dict())

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

        self.assertEqual(expected_output, output_result.hex())

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
        self.assertEqual(expected_output, output_result.hex())

    def test_parse_back_message_with_no_tlv(self):
        # Create raw message
        raw_message = b"\x40\x01\x03\x00\x01\x02\x03\x00"
        # Parse message back
        message = Message.parse_packet(raw_message)
        # Check content
        self.assertEqual(MessageType.COMMAND, message.get_message_type())
        self.assertEqual(
            MessageCommandType.TEST_CASE_SETUP, message.get_message_sub_type()
        )
        self.assertEqual(1, message.get_message_token())
        self.assertEqual(None, message.get_message_tlv_dict())

    def test_parse_back_message_with_tlv(self):
        # Create raw message
        raw_message = b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56\x00\x8f"
        # Parse message back
        message = Message.parse_packet(raw_message)
        # Check content
        self.assertEqual(MessageType.COMMAND, message.get_message_type())
        self.assertEqual(
            MessageCommandType.TEST_CASE_SETUP, message.get_message_sub_type()
        )
        self.assertEqual(1, message.get_message_token())
        self.assertDictEqual(
            {
                TlvKnownTags.TEST_REPORT: [79, 75],
                TlvKnownTags.FAILURE_REASON: [18, 52, 86],
            },
            message.get_message_tlv_dict(),
        )

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
        self.assertTrue(message_sent.check_if_ack_message_is_matching(message_received))

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
        self.assertTrue(
            message_sent.check_if_ack_message_is_matching(ack_message_received)
        )

    def test_get_crc(self):
        crc = Message.get_crc(b"@\x01\x00\x00\x00UU\x00", 2)
        self.assertEqual(b"\xc5\n", struct.pack("H", crc))


if __name__ == "__main__":
    # Start unittests
    unittest.main()
