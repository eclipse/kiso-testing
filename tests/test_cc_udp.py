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
    "msg_to_send",
    [
        (message_with_tlv),
        (message_with_no_tlv),
        (b"\x40\x01\x03\x00\x01\x02\x03\x00"),
    ],
)
def test_udp_send_valid(mock_udp_socket, msg_to_send):
    """Test message _cc_send method using context manager from Connector class.

    Validation criteria:
     - sendto is call once
    """
    with CCUdp("120.0.0.7", 5005) as udp_inst:
        udp_inst._cc_send(msg_to_send)

    mock_udp_socket.socket.sendto.assert_called_once()


@pytest.mark.parametrize(
    "expected_exception",
    [
        BlockingIOError,
        socket.timeout,
        BaseException,
    ],
)
def test_udp_recv_invalid(mocker, mock_udp_socket, expected_exception, caplog):
    """Test message _cc_receive method using context manager from Connector class.

    Validation criteria:
     - NotImplementedError raised
    """
    mocker.patch("socket.socket.recvfrom", side_effect=expected_exception)

    with CCUdp("120.0.0.7", 5005) as udp_inst:
        with caplog.at_level(logging.INTERNAL_DEBUG):
            msg_received = udp_inst._cc_receive(timeout=0.0000001)
        assert (
            f"encountered error while receiving message via {udp_inst}" in caplog.text
        )

    assert msg_received["msg"] is None
    assert udp_inst.source_addr is None


@pytest.mark.parametrize(
    "raw_data, cc_receive_param, expected_type",
    [
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (10), bytes),
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (0), bytes),
        ((b"\x40\x01\x03\x00\x01\x02\x03\x00", 36), (None), bytes),
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
        msg_received = udp_inst._cc_receive(cc_receive_param)

    assert isinstance(msg_received, dict)
    assert isinstance(msg_received["msg"], expected_type)
    assert udp_inst.source_addr == raw_data[1]
    mock_udp_socket.socket.settimeout.assert_called_once_with(cc_receive_param or 1e-6)
    mock_udp_socket.socket.recvfrom.assert_called_once()
