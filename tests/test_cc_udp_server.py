##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import socket

import pytest

from pykiso.lib.connectors.cc_udp_server import CCUdpServer
from pykiso.message import (
    Message,
    MessageCommandType,
    MessageType,
    TlvKnownTags,
)

tlv_dict_to_send = {
    TlvKnownTags.TEST_REPORT: "OK",
    TlvKnownTags.FAILURE_REASON: b"\x12\x34\x56",
}

message_with_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
    tlv_dict=tlv_dict_to_send,
)

message_with_no_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
)


@pytest.fixture
def mock_udp_socket(mocker):
    """fixture used to create mocker relative to socket object from
    socket package.
    """

    class MockSocket:
        """Class used to stub socket.socket method"""

        def __init__(self, *args, **kwargs):
            """"""
            pass

        bind = mocker.stub(name="bind")
        close = mocker.stub(name="close")
        sendto = mocker.stub(name="sendto")
        settimeout = mocker.stub(name="settimeout")
        recvfrom = mocker.stub(name="recvfrom")

    mocker.patch.object(socket, "socket", new=MockSocket)
    return socket


def test_constructor_invalid():
    """Test invalid construct with no parameters given"""

    with pytest.raises(TypeError):
        c = CCUdpServer()


def test_constructor_valid(mock_udp_socket):
    """Test a valid constructor call with valid ip and port."""
    udp_server_inst = CCUdpServer("120.0.0.7", 5005)

    assert udp_server_inst.dest_ip == "120.0.0.7"
    assert udp_server_inst.dest_port == 5005
    assert udp_server_inst.address is None
    assert udp_server_inst.max_msg_size == 256
    assert udp_server_inst.timeout == 1e-6


def test_udp_server_close(mock_udp_socket):
    """Test message _cc_close method.

    Validation criteria:
     - close is call once
    """
    udp_server_inst = CCUdpServer("120.0.0.7", 5005)
    udp_server_inst._cc_close()

    mock_udp_socket.socket.close.assert_called_once()


@pytest.mark.parametrize("msg_to_send", [(message_with_tlv), (message_with_no_tlv)])
def test_udp_server_send(mock_udp_socket, msg_to_send):
    """Test message _cc_send method using context manager from Connector class.

    Validation criteria:
     - sendto is call once
    """
    with CCUdpServer("120.0.0.7", 5005) as udp_server:
        udp_server._cc_send(msg_to_send.serialize())

    mock_udp_socket.socket.sendto.assert_called_once()


@pytest.mark.parametrize(
    "raw_data, timeout, raw, expected_type",
    [
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 5050), (10), (False), Message),
        (
            (
                b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
                2002,
            ),
            (None),
            (None),
            Message,
        ),
        ((b"\x40\x01\x03\x00\x02\x03\x00", 5050), (10), (True), bytes),
        ((b"\x40\x01\x03\x00\x02\x03\x00", 5050), (0), (True), bytes),
        ((b"\x40\x01\x03\x00\x02\x03\x00", 5050), (None), (True), bytes),
    ],
)
def test_udp_server_recv_valid(
    mocker, mock_udp_socket, raw_data, timeout, raw, expected_type
):
    """Test message _cc_receive method using context manager from Connector class.

    Validation criteria:
     - message return is type of Message
     - settimeout is call once
     - recvfrom is call once
    """
    mocker.patch("socket.socket.recvfrom", return_value=(raw_data[0], raw_data[1]))

    with CCUdpServer("120.0.0.7", 5005) as udp_server:
        msg_received = udp_server._cc_receive(timeout)

    assert isinstance(msg_received, dict)
    msg_received = msg_received.get("msg")
    if not raw:
        msg_received = Message.parse_packet(msg_received)
    assert isinstance(msg_received, expected_type)
    mock_udp_socket.socket.settimeout.assert_called_once_with(timeout or 1e-6)
    mock_udp_socket.socket.recvfrom.assert_called_once()


@pytest.mark.parametrize(
    "side_effect_mock",
    [
        BlockingIOError,
        socket.timeout,
        BaseException,
    ],
)
def test_udp_recv_invalid(mocker, mock_udp_socket, side_effect_mock, caplog):
    """Test message _cc_receive method using context manager from Connector class.

    Validation criteria:
     - correct Exception is catched
     - correct log message
     - return is None
    """
    mocker.patch("socket.socket.recvfrom", side_effect=side_effect_mock)

    with CCUdpServer("120.0.0.7", 5005) as udp_server:
        with caplog.at_level(logging.INTERNAL_DEBUG):
            msg_received = udp_server._cc_receive(timeout=0.0000001)
        assert (
            f"encountered error while receiving message via {udp_server}" in caplog.text
        )

    assert msg_received["msg"] is None
    assert udp_server.address is None
