##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
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
        halted = mocker.patch("pylink.JLink.halted", return_value=False)
        reset = mocker.stub(name="reset")
        memory_read = mocker.stub(name="memory_read")

    mocker.patch.object(pylink, "JLink", new=MockPylinkSquare)
    return pylink


def test_rtt_segger_already_open(mocker, mock_pylink_square_socket):
    mocker.patch("pylink.JLink.opened", return_value=True)

    with CCRttSegger() as cc_rtt_inst:
        pass

    mock_pylink_square_socket.JLink.open.assert_not_called()
    mock_pylink_square_socket.JLink.set_tif.assert_called_once()
    mock_pylink_square_socket.JLink.connect.assert_called_once()
    mock_pylink_square_socket.JLink.halted.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_start.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_get_buf_descriptor.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_stop.assert_called_once()
    mock_pylink_square_socket.JLink.close.assert_called_once()


def test_rtt_segger_open(mocker, mock_pylink_square_socket):
    mocker.patch("pylink.JLink.opened", return_value=False)

    with CCRttSegger() as cc_rtt_inst:
        pass

    mock_pylink_square_socket.JLink.open.assert_called_once()
    mock_pylink_square_socket.JLink.set_tif.assert_called_once()
    mock_pylink_square_socket.JLink.connect.assert_called_once()
    mock_pylink_square_socket.JLink.halted.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_start.assert_called_once()
    mock_pylink_square_socket.JLink.rtt_get_buf_descriptor.assert_called_once()
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

    assert cc_rtt_inst._log_thread_running == False
    mocker_thread_start.assert_not_called()


def test_rtt_segger_cc_open_rtt_error(
    mock_pylink_square_socket,
    mocker,
    tmpdir,
    caplog,
):
    mock_pylink_square_socket.JLink.rtt_get_num_up_buffers.return_value = 0
    mock_pylink_square_socket.JLink.halted.return_value = True
    mock_buffer = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.pylink.JLink.rtt_get_buf_descriptor",
        side_effect=[
            pylink.jlink.structs.JLinkRTTerminalBufDesc(SizeOfBuffer=0),
            pylink.errors.JLinkRTTException("code"),
        ],
    )
    mocker_thread_start = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.threading.Thread.start"
    )
    with caplog.at_level(
        logging.INFO,
    ):
        cc_rtt_inst = CCRttSegger(
            rtt_log_path=tmpdir, connection_timeout=0, rtt_log_buffer_idx=5
        )
        cc_rtt_inst._cc_open()
        assert (
            f"J-Link is halted, reset target and wait for {cc_rtt_inst.connection_timeout}s"
            in caplog.text
        )
    mock_pylink_square_socket.JLink.rtt_get_num_up_buffers.assert_called()
    assert mock_buffer.call_count == 2
    assert cc_rtt_inst._log_thread_running is True
    mocker_thread_start.assert_called()


def test_rtt_segger_cc_open_timeout(
    mock_pylink_square_socket,
    mocker,
    tmpdir,
):
    mock_pylink_square_socket.JLink.rtt_get_num_up_buffers.side_effect = (
        pylink.errors.JLinkRTTException("code")
    )
    mock_buffer = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.pylink.JLink.rtt_get_buf_descriptor",
        return_value=pylink.jlink.structs.JLinkRTTerminalBufDesc(SizeOfBuffer=1024),
    )
    with pytest.raises(Exception):
        cc_rtt_inst = CCRttSegger(rtt_log_path=tmpdir, connection_timeout=0)
        cc_rtt_inst._cc_open()

    mock_pylink_square_socket.JLink.rtt_get_num_up_buffers.assert_called()
    mock_buffer.assert_not_called()
    assert cc_rtt_inst._log_thread_running is False


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

    mock_buffer = mocker.patch(
        "pykiso.lib.connectors.cc_rtt_segger.pylink.JLink.rtt_get_buf_descriptor",
        return_value=pylink.jlink.structs.JLinkRTTerminalBufDesc(
            SizeOfBuffer=size_of_buffer
        ),
    )
    mock_rtt_read = mocker.patch("pylink.JLink.rtt_read", return_value=bytes_to_read)

    cc_rtt_inst = CCRttSegger(rtt_log_path=tmpdir)
    cc_rtt_inst._cc_open()

    assert mock_buffer.call_count == 2
    mock_rtt_read.assert_called()
    assert cc_rtt_inst._log_thread_running == True
    assert cc_rtt_inst.rtt_log_buffer_size == expected_size_of_buffer
    assert (Path(tmpdir) / "rtt.log").is_file()

    cc_rtt_inst._cc_close()
    assert cc_rtt_inst.rtt_log_thread.is_alive() == False
    assert cc_rtt_inst._log_thread_running == False
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


def test_rtt_segger_send_error(mock_pylink_square_socket, caplog):
    with CCRttSegger() as cc_rtt_inst:
        with caplog.at_level(
            logging.ERROR,
        ):
            cc_rtt_inst._cc_send(msg=[0], raw=False)
        assert (
            f"ERROR occurred while sending {len([0])} bytes on buffer {cc_rtt_inst.tx_buffer_idx}"
            in caplog.text
        )

    mock_pylink_square_socket.JLink.rtt_write.assert_not_called()


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

    assert isinstance(response, dict)
    assert isinstance(response["msg"], expected_return)


def test_rtt_segger_timeout(mocker, mock_pylink_square_socket):
    mocker.patch("pylink.JLink.rtt_read", return_value=[])

    with CCRttSegger() as cc_rtt_inst:
        response = cc_rtt_inst._cc_receive(timeout=0.010, raw=True)

    assert response["msg"] == None


@pytest.mark.parametrize(
    "addr, num_units, zone, nbits",
    [
        (0x200F202, 3, None, 32),
        (0x200F203, 1, "IDATA", 16),
        (0x200F204, 42, "DDATA", 8),
    ],
)
def test_read_target_memory(
    mocker, mock_pylink_square_socket, addr, num_units, zone, nbits
):
    mocker.patch("pylink.JLink.memory_read", return_value=[0x01, 0x02])

    with CCRttSegger() as cc_rtt_inst:
        res = cc_rtt_inst.read_target_memory(addr, num_units, zone, nbits)

    assert res == [0x01, 0x02]


@pytest.mark.parametrize(
    "exception, excepted_log",
    [
        (
            pylink.errors.JLinkException("code"),
            f"encountered error while reading memory at 0x200f202",
        ),
        (ValueError, "wrong number of bits given : must be 8, 16 or 32 bits"),
    ],
)
def test_read_target_exception(
    mocker, exception, excepted_log, mock_pylink_square_socket, caplog
):
    mocker.patch("pylink.JLink.memory_read", side_effect=exception)

    with CCRttSegger() as cc_rtt_inst:
        res = cc_rtt_inst.read_target_memory(0x200F202, 3, None, 32)

    assert res is None
    assert excepted_log in caplog.text


@pytest.mark.parametrize(
    "log_return, rtt_log_speed, expected_sleep",
    [
        (b"rtt_log", "null", 0),
        (b"rtt_log", 1000, 0.001),
        (None, 1, 1),
    ],
)
def test_receive_log(
    log_return, rtt_log_speed, expected_sleep, mocker, mock_pylink_square_socket
):
    mocker_sleep = mocker.patch("pykiso.lib.connectors.cc_rtt_segger.time.sleep")

    if rtt_log_speed:
        # rtt_log_speed explicit
        rtt_log_speed = None if rtt_log_speed == "null" else rtt_log_speed
        cc_rtt_inst = CCRttSegger(rtt_log_speed=rtt_log_speed)
    else:
        # rtt_log_speed not passed
        cc_rtt_inst = CCRttSegger()

    def mock_jlink_rtt_read(rtt_log_buffer_idx, rtt_log_buffer_size):
        """Check input, stop while loop and return mock log value"""
        assert rtt_log_buffer_idx == "log_buffer_idx"
        assert rtt_log_buffer_size == "log_buffer_size"

        cc_rtt_inst._log_thread_running = False
        return log_return

    jlink_mock = mocker.Mock()
    jlink_mock.rtt_read = mock_jlink_rtt_read
    cc_rtt_inst.jlink = jlink_mock
    mock_rtt_log = cc_rtt_inst.rtt_log = mocker.Mock()

    cc_rtt_inst.rtt_log_buffer_idx = "log_buffer_idx"
    cc_rtt_inst.rtt_log_buffer_size = "log_buffer_size"
    cc_rtt_inst._log_thread_running = True
    cc_rtt_inst.rtt_configured = True

    cc_rtt_inst.receive_log()

    mocker_sleep.assert_called_once_with(expected_sleep)
    if log_return:
        mock_rtt_log.debug.assert_called_once_with("rtt_log")


def test_reset_jlink(mocker):

    cc_rtt_inst = CCRttSegger()
    mock_jlink = mocker.Mock()
    cc_rtt_inst.jlink = mock_jlink

    cc_rtt_inst.reset_target()

    cc_rtt_inst.jlink.reset.assert_called_once()
    cc_rtt_inst.jlink.enable_reset_pulls_reset.assert_called_once()
