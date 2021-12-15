##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import socket

import pytest

from pykiso.lib.connectors.cc_udp import CCUdp
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

        close = mocker.stub(name="close")
        sendto = mocker.stub(name="sendto")
        settimeout = mocker.stub(name="settimeout")
        recvfrom = mocker.stub(name="recvfrom")

    mocker.patch.object(socket, "socket", new=MockSocket)
    return socket


def test_constructor_invalid():
    """Test invalid construct with no parameters given"""

    with pytest.raises(TypeError):
        c = CCUdp()


def test_constructor_valid(mock_udp_socket):
    """Test a valid constructor call with valid ip and port."""
    udp_inst = CCUdp("120.0.0.7", 5005)

    assert udp_inst.dest_ip == "120.0.0.7"
    assert udp_inst.dest_port == 5005
    assert udp_inst.max_msg_size == 256
    assert udp_inst.timeout == 1e-6


def test_udp_close(mock_udp_socket):
    """Test message _cc_close method.

    Validation criteria:
     - close is call once
    """
    udp_inst = CCUdp("120.0.0.7", 5005)
    udp_inst._cc_open()
    udp_inst._cc_close()

    mock_udp_socket.socket.close.assert_called_once()


@pytest.mark.parametrize(
    "msg_to_send, raw_state",
    [
        (message_with_tlv, False),
        (message_with_no_tlv, False),
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", True),
    ],
)
def test_udp_send_valid(mock_udp_socket, msg_to_send, raw_state):
    """Test message _cc_send method using context manager from Connector class.

    Validation criteria:
     - sendto is call once
    """
    with CCUdp("120.0.0.7", 5005) as udp_inst:
        udp_inst._cc_send(msg_to_send, raw=raw_state)

    mock_udp_socket.socket.sendto.assert_called_once()


@pytest.mark.parametrize(
    "raw_state",
    [
        True,
        False,
    ],
)
def test_udp_recv_invalid(mocker, mock_udp_socket, raw_state):
    """Test message _cc_receive method using context manager from Connector class.

    Validation criteria:
     - NotImplementedError raised
    """
    mocker.patch("socket.socket.recvfrom", return_value=None)

    with CCUdp("120.0.0.7", 5005) as udp_inst:
        msg_received = udp_inst._cc_receive(timeout=0.0000001, raw=raw_state)

    assert msg_received == None
    assert udp_inst.source_addr == None


@pytest.mark.parametrize(
    "raw_data, cc_receive_param, expected_type",
    [
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 1002), (10, False), Message),
        (
            (
                b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
                4000,
            ),
            (None, None),
            Message,
        ),
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (10, True), bytes),
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (0, True), bytes),
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (None, True), bytes),
    ],
)
def test_udp_recv_valid(
    mocker, mock_udp_socket, raw_data, cc_receive_param, expected_type
):
    """Test message _cc_receive method using context manager from Connector class.

    Validation criteria:
     - message return is type of Message
     - settimeout is call once
     - recvfrom is call once
    """
    mocker.patch("socket.socket.recvfrom", return_value=raw_data)

    with CCUdp("120.0.0.7", 5005) as udp_inst:
        msg_received = udp_inst._cc_receive(*cc_receive_param)

    assert isinstance(msg_received, expected_type) == True
    assert udp_inst.source_addr == raw_data[1]
    mock_udp_socket.socket.settimeout.assert_called_once_with(
        cc_receive_param[0] or 1e-6
    )
    mock_udp_socket.socket.recvfrom.assert_called_once()
