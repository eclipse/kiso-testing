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
import logging

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


def test_reset_board_success(mocker):
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

    message = lauterbach_inst._cc_receive()
    assert message.serialize() == msg_received

    # reset_board can be called only after the receive function was called.
    lauterbach_inst.reset_board()

    assert lauterbach_inst.reset_flag == False
