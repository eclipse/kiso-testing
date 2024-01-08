##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import threading
import time
from queue import Queue

import pytest

from pykiso.can_message import CanMessage
from pykiso.lib.auxiliaries.can_auxiliary import CanAuxiliary
from pykiso.lib.connectors.cc_pcan_can.cc_pcan_can import CCPCanCan


class TestCanAux:

    net_aux_instance = None

    @pytest.fixture(scope="function")
    def can_aux_instance(self):
        channel = CCPCanCan()
        TestCanAux.can_aux_instance = CanAuxiliary(
            channel, "./examples/test_can/simple.dbc"
        )
        return TestCanAux.can_aux_instance

    def test_send_message(self, can_aux_instance, mocker):

        message_name = "Message_1"
        message_signals = {"signal_a": 1, "signal_b": 5}
        cc_send_mock = mocker.patch.object(can_aux_instance.channel, "cc_send")
        can_aux_instance.send_message(message_name, message_signals)
        cc_send_mock.assert_called_with(b"\x01\x05\x00\x00", remote_id=16)

    def test_send_message_with_str_signal(self, can_aux_instance, mocker):
        message_name = "Message_1"
        message_signals = {"signal_a": "a", "signal_b": 5}
        cc_send_mock = mocker.patch.object(can_aux_instance.channel, "cc_send")
        can_aux_instance.send_message(message_name, message_signals)
        cc_send_mock.assert_called_with(b"a\x05\x00\x00", remote_id=16)

    def test_send_message_with_wrong_msg_name(self, can_aux_instance, mocker):
        message_name = "Message_2"
        message_signals = {"signal_a": 1, "signal_b": 5}
        with pytest.raises(
            ValueError, match=r"Message_2 is not a message defined in the DBC file."
        ):
            can_aux_instance.send_message(message_name, message_signals)

    def test_get_message_with_empty_queue(self, can_aux_instance):
        result = can_aux_instance.get_last_message("Simple_Msg")
        assert result is None

    def test_get_last_message(self, can_aux_instance):
        can_aux_instance.can_messages["Simple_Msg"] = Queue(maxsize=1)
        can_aux_instance.can_messages["Simple_Msg"].put_nowait(
            CanMessage("Simple_Msg", {"a": 5}, 5)
        )

        can_aux_instance.can_messages["Simple_Msg1"] = Queue(maxsize=1)
        can_aux_instance.can_messages["Simple_Msg1"].put_nowait(
            CanMessage("Simple_Msg1", {"a": 4}, 4)
        )

        result = can_aux_instance.get_last_message("Simple_Msg")

        assert result.name == "Simple_Msg"
        assert result.signals == {"a": 5}
        assert result.timestamp == 5
        assert can_aux_instance.can_messages["Simple_Msg"].full()

    def test_get_last_signal(self, can_aux_instance):
        can_aux_instance.can_messages["Simple_Msg"] = Queue(maxsize=1)
        can_aux_instance.can_messages["Simple_Msg"].put_nowait(
            CanMessage("Simple_Msg", {"a": 5}, 5)
        )

        result = can_aux_instance.get_last_signal("Simple_Msg", "a")

        assert result == 5
        assert can_aux_instance.can_messages["Simple_Msg"].full()

    def test_get_last_signal_with_wrong_signal_name(self, can_aux_instance):
        can_aux_instance.can_messages["Simple_Msg"] = Queue(maxsize=1)
        can_aux_instance.can_messages["Simple_Msg"].put_nowait(
            CanMessage("Simple_Msg", {"a": 5}, 5)
        )

        result = can_aux_instance.get_last_signal("Simple_Msg", "b")

        assert result is None
        assert can_aux_instance.can_messages["Simple_Msg"].full()

    def test_get_last_signal_with_empty_queue(self, can_aux_instance):
        result = can_aux_instance.get_last_signal("Simple_Msg", "b")
        assert result is None

    def test_wait_for_message(self, can_aux_instance):
        result = []
        msg_to_send = CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 5)
        send_t = threading.Thread(
            target=self.send_message, args=[can_aux_instance, msg_to_send]
        )
        recv_t = threading.Thread(
            target=self.wait_for_receive_message,
            args=[can_aux_instance, 1, msg_to_send.name, result],
        )

        recv_t.start()
        time.sleep(0.2)
        send_t.start()
        send_t.join()
        recv_t.join()

        assert result[0].name == msg_to_send.name
        assert result[0].signals == msg_to_send.signals
        assert result[0].timestamp == msg_to_send.timestamp
        assert can_aux_instance.can_messages[msg_to_send.name].full()

    def test_wait_for_message_with_delayed_msg(self, can_aux_instance):
        result = []
        msg_to_send = CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 5)
        old_msg = CanMessage("Message_1", {"signal_a": 5, "signal_b": 6}, 7)
        can_aux_instance.can_messages["Message_1"] = Queue(maxsize=1)
        can_aux_instance.can_messages[old_msg.name].put_nowait(old_msg)
        recv_t = threading.Thread(
            target=self.wait_for_receive_message,
            args=[can_aux_instance, 0.1, msg_to_send.name, result],
        )

        recv_t.start()
        time.sleep(0.5)
        recv_t.join()

        assert result[0] is None
        msg_in_the_queue = can_aux_instance.can_messages["Message_1"].get_nowait()
        assert msg_in_the_queue.name == old_msg.name
        assert msg_in_the_queue.signals == old_msg.signals
        assert msg_in_the_queue.timestamp == old_msg.timestamp

    def test_wait_for_match_signals(self, can_aux_instance):
        result = []
        messages_to_send = [
            CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 3),
            CanMessage("Message_1", {"signal_a": 4, "signal_b": 5}, 6),
            CanMessage("Message_1", {"signal_a": 7, "signal_b": 8}, 9),
        ]

        can_aux_instance.can_messages["Message_1"] = Queue(maxsize=1)
        send_t = threading.Thread(
            target=self.send_multiple_messages_with_timeout,
            args=[can_aux_instance, messages_to_send, 0.2],
        )
        recv_t = threading.Thread(
            target=self.wait_for_match_msg,
            args=[can_aux_instance, 3, "Message_1", {"signal_a": 7}, result],
        )

        recv_t.start()
        time.sleep(0.2)
        send_t.start()
        send_t.join()
        recv_t.join()

        assert result[0].name == "Message_1"
        assert result[0].signals == {"signal_a": 7, "signal_b": 8}
        assert result[0].timestamp == 9

    def test_wait_for_match_signal_with_wrong_signals(self, can_aux_instance):
        result = []
        messages_to_send = [
            CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 3),
            CanMessage("Message_1", {"signal_a": 4, "signal_b": 5}, 6),
            CanMessage("Message_1", {"signal_a": 7, "signal_b": 8}, 9),
        ]

        can_aux_instance.can_messages["Message_1"] = Queue(maxsize=1)
        send_t = threading.Thread(
            target=self.send_multiple_messages_with_timeout,
            args=[can_aux_instance, messages_to_send, 0.2],
        )
        recv_t = threading.Thread(
            target=self.wait_for_match_msg,
            args=[can_aux_instance, 3, "Message_1", {"signal_a": 12}, result],
        )

        recv_t.start()
        time.sleep(0.2)
        send_t.start()
        send_t.join()
        recv_t.join()

        assert result[0] is None

    def test_wait_for_match_signal_without_send_messages(self, can_aux_instance):
        result = []
        recv_t = threading.Thread(
            target=self.wait_for_match_msg,
            args=[can_aux_instance, 3, "Message_1", {"signal_a": 12}, result],
        )

        recv_t.start()
        recv_t.join()

        assert result[0] is None

    def send_message(self, can_aux, msg_to_send):
        if can_aux.can_messages.get(msg_to_send.name, None) is None:
            can_aux.can_messages[msg_to_send.name] = Queue(maxsize=1)
        if can_aux.can_messages[msg_to_send.name].full():
            can_aux.can_messages[msg_to_send.name].get_nowait()
        can_aux.can_messages[msg_to_send.name].put_nowait(msg_to_send)

    def wait_for_receive_message(self, can_aux, timeout, msg_name, result):
        recv_msg = can_aux.wait_for_message(msg_name, timeout)
        result.append(recv_msg)

    def send_multiple_messages_with_timeout(
        self, can_aux, messages_to_send, timeout_between_messages
    ):
        for msg_to_send in messages_to_send:
            if can_aux.can_messages.get(msg_to_send.name, None) is None:
                can_aux.can_messages[msg_to_send.name] = Queue(maxsize=1)
            if can_aux.can_messages[msg_to_send.name].full():
                can_aux.can_messages[msg_to_send.name].get_nowait()
            can_aux.can_messages[msg_to_send.name].put_nowait(msg_to_send)
            time.sleep(timeout_between_messages)

    def wait_for_match_msg(self, can_aux, timeout, msg_name, expected_signals, result):
        recv_msg = can_aux.wait_to_match_message_with_signals(
            msg_name, expected_signals, timeout
        )
        result.append(recv_msg)

    def test_receive_message_with_empty_queue(self, can_aux_instance, mocker):
        simple_msg = {
            "msg": bytearray(b"\x01\x05\x00\x00"),
            "remote_id": 16,
            "timestamp": 2,
        }
        cc_receive_mock = mocker.patch.object(
            self.can_aux_instance.channel, "cc_receive", return_value=simple_msg
        )
        msg_obj_magic_mock = mocker.MagicMock()
        msg_obj_magic_mock.name = "Message_1"
        get_msg_by_frame_mock = mocker.patch.object(
            can_aux_instance.parser.dbc,
            "get_message_by_frame_id",
            return_value=msg_obj_magic_mock,
        )
        parser_decode_mock = mocker.patch.object(
            can_aux_instance.parser,
            "decode",
            return_value={"signal_a": 1, "signal_b": 5},
        )

        can_aux_instance._receive_message(2)

        cc_receive_mock.assert_called_with(timeout=2)
        get_msg_by_frame_mock.assert_called_with(16)
        parser_decode_mock.assert_called_with(bytearray(b"\x01\x05\x00\x00"), 16)
        assert can_aux_instance.can_messages["Message_1"].full()
        msg_int_the_queue = can_aux_instance.can_messages["Message_1"].get_nowait()
        assert msg_int_the_queue.name == "Message_1"
        assert msg_int_the_queue.signals == {"signal_a": 1, "signal_b": 5}
        assert msg_int_the_queue.timestamp == 2

    def test_receive_message_with_full_queue(self, can_aux_instance, mocker):
        simple_msg = {
            "msg": bytearray(b"\x01\x05\x00\x00"),
            "remote_id": 16,
            "timestamp": 2,
        }
        cc_receive_mock = mocker.patch.object(
            self.can_aux_instance.channel, "cc_receive", return_value=simple_msg
        )
        msg_obj_magic_mock = mocker.MagicMock()
        msg_obj_magic_mock.name = "Message_1"
        get_msg_by_frame_mock = mocker.patch.object(
            can_aux_instance.parser.dbc,
            "get_message_by_frame_id",
            return_value=msg_obj_magic_mock,
        )
        parser_decode_mock = mocker.patch.object(
            can_aux_instance.parser,
            "decode",
            return_value={"signal_a": 1, "signal_b": 5},
        )
        can_aux_instance.can_messages["Message_1"] = Queue(maxsize=1)
        can_aux_instance.can_messages["Message_1"].put_nowait(
            CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 3)
        )

        can_aux_instance._receive_message(2)

        cc_receive_mock.assert_called_with(timeout=2)
        get_msg_by_frame_mock.assert_called_with(16)
        parser_decode_mock.assert_called_with(bytearray(b"\x01\x05\x00\x00"), 16)
        assert can_aux_instance.can_messages["Message_1"].full()
        msg_int_the_queue = can_aux_instance.can_messages["Message_1"].get_nowait()
        assert msg_int_the_queue.name == "Message_1"
        assert msg_int_the_queue.signals == {"signal_a": 1, "signal_b": 5}
        assert msg_int_the_queue.timestamp == 2

    def test_decode_msg(self, can_aux_instance, mocker):
        parser_dbc_decode_mock = mocker.patch.object(
            can_aux_instance.parser.dbc, "decode_message"
        )

        can_aux_instance.parser.decode(bytearray(b"\x01\x05\x00\x00"), 16)
        parser_dbc_decode_mock.assert_called_with(
            16, bytearray(b"\x01\x05\x00\x00"), decode_choices=False
        )
