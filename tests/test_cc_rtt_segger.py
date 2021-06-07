##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

from itertools import cycle
from pathlib import Path

import pylink
import pytest

from pykiso.lib.connectors.cc_rtt_segger import CCRttSegger
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
def mock_pylink_square_socket(mocker):
    """fixture used to create mocker relative to socket object from
    socket package.
    """

    class MockPylinkSquare:
        """Class used to stub socket.socket method"""

        def __init__(self, *args, **kwargs):
            """Constructor
            Define the message to be return
            """
            self.msg_received = cycle(
                [
                    b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56\x00\x8f",
                    b"\x40\x01\x03\x00\x01\x02\x03\x00\xd6\xcd",
                ]
            )

            self.current_msg = next(self.msg_received)

        def rtt_read(self, buffer_index, num_bytes):
            """Mock rtt_read()"""
            read = list(self.current_msg[:num_bytes])
            self.current_msg = self.current_msg[num_bytes:]

            if len(self.current_msg) == 0:
                self.current_msg = next(self.msg_received)

            return read

        opened = mocker.stub(name="opened")
        open = mocker.stub(name="open")
        rtt_write = mocker.stub(name="rtt_write")
        set_tif = mocker.stub(name="set_tif")
        connect = mocker.stub(name="connect")
        rtt_start = mocker.stub(name="rtt_start")
        rtt_stop = mocker.stub(name="rtt_stop")
        close = mocker.stub(name="close")
        rtt_get_num_up_buffers = mocker.stub(name="rtt_get_num_up_buffers")
        rtt_get_num_down_buffers = mocker.stub(name="rtt_get_num_down_buffers")
        rtt_get_buf_descriptor = mocker.stub(name="rtt_get_buf_descriptor")

    mocker.patch.object(pylink, "JLink", new=MockPylinkSquare)
    return pylink


def test_rtt_segger_already_open(mocker, mock_pylink_square_socket):
    mocker.patch(
        "pylink.JLink.opened",
        return_value=True,
    )

    with CCRttSegger() as cc_rtt_inst:
        pass

    mock_pylink_square_socket.JLink.open.assert_not_called()
    mock_pylink_square_socket.JLink.set_tif.assert_called_once()
    mock_pylink_square_socket.JLink.connect.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_start.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_stop.assert_called_once()
    mock_pylink_square_socket.JLink.close.assert_called_once()


def test_rtt_segger_open(mocker, mock_pylink_square_socket):
    mocker.patch(
        "pylink.JLink.opened",
        return_value=False,
    )

    with CCRttSegger() as cc_rtt_inst:
        pass

    mock_pylink_square_socket.JLink.open.assert_called_once()
    mock_pylink_square_socket.JLink.set_tif.assert_called_once()
    mock_pylink_square_socket.JLink.connect.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_start.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_stop.assert_called_once()
    mock_pylink_square_socket.JLink.close.assert_called_once()


def test_rtt_segger_close_invalid(mock_pylink_square_socket):

    cc_rtt_inst = CCRttSegger()
    cc_rtt_inst._cc_close()

    mock_pylink_square_socket.JLink.rtt_stop.assert_not_called()
    mock_pylink_square_socket.JLink.close.assert_not_called()


def test_rtt_segger_close_valid(mock_pylink_square_socket):

    cc_rtt_inst = CCRttSegger()
    cc_rtt_inst._cc_open()
    cc_rtt_inst._cc_close()

    mock_pylink_square_socket.JLink.rtt_stop.assert_called_once()
    mock_pylink_square_socket.JLink.close.assert_called_once()


def test_rtt_segger_rtt_logger_not_running(mock_pylink_square_socket, mocker):

    mocker_thread_start = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.threading.Thread.start"
    )
    cc_rtt_inst = CCRttSegger()
    cc_rtt_inst._cc_open()

    assert cc_rtt_inst._is_running == False
    mocker_thread_start.assert_not_called()


@pytest.mark.parametrize(
    "size_of_buffer, expected_size_of_buffer, bytes_to_read, rtt_log",
    [
        (0, 1024, b"\x30", "0"),
        (1000, 1000, b"\x30", "0"),
    ],
)
def test_rtt_segger_rtt_logger_running(
    mock_pylink_square_socket,
    mocker,
    size_of_buffer,
    expected_size_of_buffer,
    bytes_to_read,
    rtt_log,
    tmpdir,
):

    mocker_buffer = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.pylink.JLink.rtt_get_buf_descriptor",
        return_value=pylink.jlink.structs.JLinkRTTerminalBufDesc(
            SizeOfBuffer=size_of_buffer
        ),
    )
    mocker_rtt_read = mocker.patch("pylink.JLink.rtt_read", return_value=bytes_to_read)

    cc_rtt_inst = CCRttSegger(rtt_log_path=tmpdir)
    cc_rtt_inst._cc_open()

    mocker_buffer.assert_called_once()
    mocker_rtt_read.assert_called()
    assert cc_rtt_inst._is_running == True
    assert cc_rtt_inst.rtt_log_buffer_size == expected_size_of_buffer
    assert (Path(tmpdir) / "rtt.log").is_file()

    cc_rtt_inst._cc_close()
    assert cc_rtt_inst._is_running == False
    assert rtt_log in (Path(tmpdir) / "rtt.log").read_text()


@pytest.mark.parametrize(
    "msg_to_send, raw_state",
    [
        (message_with_tlv, False),
        (message_with_no_tlv, False),
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", True),
    ],
)
def test_rtt_segger_send(mock_pylink_square_socket, msg_to_send, raw_state):
    with CCRttSegger() as cc_rtt_inst:
        cc_rtt_inst._cc_send(msg=msg_to_send, raw=raw_state)

    mock_pylink_square_socket.JLink.rtt_write.assert_called_once()


@pytest.mark.parametrize(
    "timeout, raw, expected_return",
    [
        (10, False, Message),
        (0.500, True, bytes),
    ],
)
def test_rtt_segger_receive(
    mocker, mock_pylink_square_socket, timeout, raw, expected_return
):

    with CCRttSegger() as cc_rtt_inst:
        response = cc_rtt_inst._cc_receive(timeout=timeout, raw=raw)

    assert isinstance(response, expected_return)


def test_rtt_segger_timeout(mocker, mock_pylink_square_socket):
    mocker.patch("pylink.JLink.rtt_read", return_value=[])

    with CCRttSegger() as cc_rtt_inst:
        response = cc_rtt_inst._cc_receive(timeout=0.010, raw=True)

    assert response == None
