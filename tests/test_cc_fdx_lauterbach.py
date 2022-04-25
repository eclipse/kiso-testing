##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

""" Test module for CCLauterbach.py
"""
import time
import logging
import pytest
from pykiso.lib.connectors.cc_fdx_lauterbach import CCFdxLauterbach
from pykiso.message import Message


class Mock_t32_api:
    """Class used to stub T32_api method"""

    def __init__(self, **kwargs):
        self.t32_Init = 0
        self.t32_Attach = 0
        self.t32_Cmd = 0
        self.t32_PracticeState = 0
        self.t32_PracticeState_error = 0
        self.t32_Config = 0
        self.t32_Ping = 0
        self.t32_Fdx_Open = 0
        self.t32_Fdx_Close = 0
        self.t32_ResetCPU = 0
        self.t32_Fdx_SendPoll = 0
        self.t32_Fdx_ReceivePoll_msg = b""
        self.t32_Go = 0
        self.t32_Stop = 0

    def T32_Init(self):
        return self.t32_Init

    def T32_Attach(self, device: int):
        return self.t32_Attach

    def T32_Cmd(self, command: bytes):
        return self.t32_Cmd

    def T32_GetPracticeState(self, state_pointer):
        state_pointer._obj.value = self.t32_PracticeState
        return self.t32_PracticeState_error

    def T32_Config(self, command, value):
        return self.t32_Config

    def T32_Ping(self):
        return self.t32_Ping

    def T32_Fdx_Open(self, buffer, mode):
        return self.t32_Fdx_Open

    def T32_Fdx_Close(self, fdx_id):
        return self.t32_Fdx_Close

    def T32_ResetCPU(self):
        return self.t32_ResetCPU

    def T32_Fdx_SendPoll(self, fdx_id, buffer, width, length):
        return self.t32_Fdx_SendPoll

    def T32_Fdx_ReceivePoll(self, fdx_id, buffer, width, length):
        buffer.contents.raw = self.t32_Fdx_ReceivePoll_msg
        return len(self.t32_Fdx_ReceivePoll_msg)

    def T32_Go(self):
        return self.t32_Go

    def T32_Stop(self):
        return self.t32_Stop


def test_open_success(mocker):
    """Test the open function"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )
    mocker.patch("ctypes.CDLL", return_value=Mock_t32_api())
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)

    cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is True


def test_open_fail_to_init(mocker):
    """Test the open function with failed init from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Init = -1
    mock_t32_api.t32_Ping = -1
    mocker.patch("ctypes.CDLL", return_value=mock_t32_api)
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)

    cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False


@pytest.mark.parametrize(
    "side_effect_ctypes,side_effect_subprocess, expected_log",
    [
        (Exception, None, "Unable to open Trace32:"),
        (None, Exception, "Unable to open Trace32"),
    ],
)
def test_open_exceptions(
    mocker, caplog, side_effect_ctypes, side_effect_subprocess, expected_log
):
    """Test the open function with failed init from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )
    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Init = 1
    mock_t32_api.t32_Ping = -1
    mocker.patch("ctypes.CDLL", side_effect=side_effect_ctypes)
    mocker.patch("subprocess.Popen", side_effect=side_effect_subprocess)

    with caplog.at_level(
        logging.ERROR,
    ):
        cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False
    assert expected_log in caplog.text


def test_open_fail_to_ping(mocker):
    """Test the open function with failed ping from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Ping = -1
    mocker.patch("ctypes.CDLL", return_value=mock_t32_api)
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)

    cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False


def test_open_fail_to_load_script(mocker):
    """Test the open function with failed loading a script from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_PracticeState_error = -1
    mocker.patch("ctypes.CDLL", return_value=mock_t32_api)
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)

    cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False


def test_open_fail_to_close_fdx_communication(mocker, caplog):
    """Test the open function with failed fdx communication from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api_fdxout = mocker.patch.object(Mock_t32_api, "T32_Fdx_Open")
    mock_t32_api_fdxout.side_effect = [1, -1]
    mock_t32_api = Mock_t32_api()

    mocker.patch("ctypes.CDLL", return_value=mock_t32_api)
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)
    with caplog.at_level(
        logging.ERROR,
    ):
        cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False
    assert "No FDXout buffer" in caplog.text


def test_open_fail_to_open_fdx_communication(mocker):
    """Test the open function with failed fdx communication from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_Open = -1
    mocker.patch("ctypes.CDLL", return_value=mock_t32_api)
    mocker.patch("subprocess.Popen", return_value=1234)
    mocker.patch("time.sleep", return_value=None)

    cc_opened = lauterbach_inst._cc_open()
    assert cc_opened is False


def test_cc_close(mocker, caplog):
    """Test the __cc_close function"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_Close = 1
    mock_t32_api.t32_ResetCPU = 2
    lauterbach_inst.t32_api = mock_t32_api
    mock_load_script = mocker.patch.object(lauterbach_inst, "load_script")

    with caplog.at_level(logging.DEBUG):
        cc_closed = lauterbach_inst._cc_close()

    assert (
        f"Disconnected from FDX {lauterbach_inst.fdxin} with state {mock_t32_api.t32_Fdx_Close}"
        in caplog.text
    )
    assert (
        f"Disconnected from FDX {lauterbach_inst.fdxout} with state {mock_t32_api.t32_Fdx_Close}"
        in caplog.text
    )
    assert f"Reset the CPU with state {mock_t32_api.t32_ResetCPU}" in caplog.text
    mock_load_script.assert_called()


def test_load_script_success(mocker):
    """Test the load script function"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mocker.patch("time.sleep", return_value=None)
    lauterbach_inst.t32_api = Mock_t32_api()
    load_script_err = lauterbach_inst.load_script("script.cmm")
    assert load_script_err == 0


def test_load_response_fail(caplog, mocker):
    """Test the load script function"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mocker.patch("time.sleep", return_value=None)
    lauterbach_inst.t32_api = Mock_t32_api()
    lauterbach_inst.t32_api.t32_PracticeState_error = -1  # Error
    lauterbach_inst.t32_api.t32_PracticeState = 1  # Running

    with caplog.at_level(
        logging.ERROR, logger="pykiso.lib.connectors.cc_fdx_lauterbach.py.log"
    ):
        load_script_err = lauterbach_inst.load_script("script.cmm")

    assert load_script_err == -1
    assert "Abort execution" in caplog.text


def test_load_script_fail_cmd(mocker):
    """Test the load script function with failed sending a command from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mocker.patch("time.sleep", return_value=None)
    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Cmd = -1
    lauterbach_inst.t32_api = mock_t32_api

    load_script_err = lauterbach_inst.load_script("script.cmm")
    assert load_script_err == -1


def test_load_script_fail_T32_GetPracticeState(mocker):
    """Test the load script function with failing while getting practice state from t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    mocker.patch("time.sleep", return_value=None)
    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_PracticeState_error = -1
    lauterbach_inst.t32_api = mock_t32_api

    load_script_err = lauterbach_inst.load_script("script.cmm")
    assert load_script_err == -1


def test_send_raw_bytes():
    """Test send raw bytes using t32 api"""
    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    msg = b"a123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`ab"

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_SendPoll = len(msg)
    lauterbach_inst.t32_api = mock_t32_api

    poll_len = lauterbach_inst._cc_send(msg, raw=True)
    assert poll_len == len(msg)


def test_send_message():
    """Test send a Message using t32 api"""
    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    msg = Message()
    expected_len = len(msg.serialize())

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_SendPoll = expected_len
    lauterbach_inst.t32_api = mock_t32_api

    poll_len = lauterbach_inst._cc_send(msg)
    assert poll_len == expected_len


def test_send_message_exception(caplog, mock_msg):
    """Test send a Message using t32 api"""
    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    msg = b"0x3A"
    expected_len = len(msg)

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_SendPoll = -3
    lauterbach_inst.t32_api = mock_t32_api
    with caplog.at_level(
        logging.ERROR,
    ):
        poll_len = lauterbach_inst._cc_send(msg, True)
    assert poll_len == -3
    assert (
        f"ERROR occurred while sending {expected_len} bytes on {lauterbach_inst.fdxout}"
        in caplog.text
    )


def test_receive():
    """Test receive message using t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    msg_received = Message().serialize()

    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_ReceivePoll_msg = msg_received
    lauterbach_inst.t32_api = mock_t32_api

    message = lauterbach_inst._cc_receive()
    assert message.serialize() == msg_received


@pytest.mark.parametrize(
    "side_effect, reset_Flag",
    [
        ([None, None], True),
        ([-1], False),
        ([0, 0, 0], False),
    ],
)
def test_receive_outside(mocker, side_effect, reset_Flag, caplog):
    """Test receive message using t32 api"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )
    lauterbach_inst.reset_flag = reset_Flag
    mock_t32_api_ReceivePoll = mocker.patch.object(Mock_t32_api, "T32_Fdx_ReceivePoll")
    mock_t32_api_ReceivePoll.side_effect = side_effect
    mocker.patch.object(time, "perf_counter", side_effect=[1, 21])

    mock_t32_api = Mock_t32_api()

    lauterbach_inst.t32_api = mock_t32_api
    with caplog.at_level(logging.ERROR):
        message = lauterbach_inst._cc_receive()
    assert message is None

    if len(side_effect) == 1:
        assert (
            f"ERROR occurred while listening channel {lauterbach_inst.fdxin} with buffer: "
            in caplog.text
        )


def test_reset_board_success(mocker, caplog):
    """Test the open function"""

    lauterbach_inst = CCFdxLauterbach(
        "PATH/TO/T32_EXE.exe",
        "C:/PATH_OF_T32_CONFIG.t32",
        "C:/PATH_OF_fdx.cmm",
        "C:/PATH_OF_reset.cmm",
        "C:/PATH_OF_fdx_clear.cmm",
        "C:/PATH_OF_inTest_reset.cmm",
        "C:/T32/demo/api/capi/dll/t32api.dll",
        "20000",
        "localhost",
        "1024",
        1,
    )

    msg_received = Message().serialize()
    mock_t32_api = Mock_t32_api()
    mock_t32_api.t32_Fdx_ReceivePoll_msg = msg_received
    lauterbach_inst.t32_api = mock_t32_api
    mock_time_sleep = mocker.patch("time.sleep")

    message = lauterbach_inst._cc_receive()
    assert message.serialize() == msg_received

    # reset_board can be called only after the receive function was called.
    mock_t32_api_fdx_open = mocker.patch.object(Mock_t32_api, "T32_Fdx_Open")
    mock_t32_api_fdx_open.return_value = -1
    with caplog.at_level(
        logging.ERROR,
    ):
        lauterbach_inst.reset_board()
    assert lauterbach_inst.reset_flag == False
    assert mock_t32_api_fdx_open.call_count == 2
    assert "No FDXin buffer" in caplog.text
    assert "No FDXout buffer" in caplog.text
