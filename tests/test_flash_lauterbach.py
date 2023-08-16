##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import ctypes
import logging
import subprocess

import psutil
import pytest

from pykiso.lib.connectors.flash_lauterbach import LauterbachFlasher

LOGGER = logging.getLogger(__name__)

SCRIPT_CONTENT = """
SET FLASH MEMORY ADDR 0xFFFFF/0x00000
FLASH myfolder/binary.hex
"""


@pytest.fixture
def tmp_script_file(tmp_path):
    f = tmp_path / "fake_script.cmm"
    f.write_text(SCRIPT_CONTENT)
    return f


class StubTrace32Api:
    @staticmethod
    def T32_Config(cfg_type, node):
        pass

    @staticmethod
    def T32_Init():
        return 0

    @staticmethod
    def T32_Attach(device):
        pass

    @staticmethod
    def T32_Ping():
        return 0

    @staticmethod
    def T32_Exit():
        return 0

    @staticmethod
    def T32_Cmd(cmd):
        return 0

    @staticmethod
    def T32_GetPracticeState(state_var):
        return 1

    @staticmethod
    def T32_GetMessage(msg_var, state_var):
        return 0


class StubProcess:
    @staticmethod
    def kill():
        pass

    @staticmethod
    def name():
        return "Trace32App.exe"

    @staticmethod
    def pid():
        return "3022"

    @staticmethod
    def wait(timeout=0):
        return 0


@pytest.fixture
def mock_subprocess(mocker):
    def popen_stub(startargs):
        return StubProcess()

    mocker.patch.object(subprocess, "Popen", new=popen_stub)
    return subprocess


@pytest.fixture
def mock_remote_api(mocker):
    def load_library_stub(path):
        return StubTrace32Api()

    mocker.patch.object(ctypes.cdll, "LoadLibrary", new=load_library_stub)
    return ctypes.cdll


@pytest.fixture
def mock_psutil(mocker):
    def process_iter_stub():
        return [StubProcess()]

    mocker.patch.object(psutil, "process_iter", new=process_iter_stub)
    return psutil


@pytest.fixture
def lauterbach_flasher(tmp_script_file):

    return LauterbachFlasher(
        t32_exc_path="fake_path",
        t32_config="fake_config_file",
        t32_script_path=tmp_script_file,
        t32_api_path="fake_api_path",
        port="20000",
        node="localhost",
        packlen="1024",
        device=1,
    )


class CtypeTypeMock:
    def __init__(self, value) -> None:
        self.value = value


def test_constructor(lauterbach_flasher, tmp_script_file):
    assert lauterbach_flasher.device == 1
    assert lauterbach_flasher.packlen == "1024"
    assert lauterbach_flasher.node == "localhost"
    assert lauterbach_flasher.port == "20000"
    assert lauterbach_flasher.t32_api_path == "fake_api_path"
    assert lauterbach_flasher.t32_script_path == tmp_script_file
    assert lauterbach_flasher.t32_start_args == ["fake_path", "-c", "fake_config_file"]


def test_open(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api
):
    lauterbach_flasher.loadup_wait_time = 0
    with caplog.at_level(logging.INTERNAL_DEBUG):
        lauterbach_flasher.open()
        assert (
            "Trace32 process open with arguments ['fake_path', '-c', 'fake_config_file']"
            in caplog.text
        )
        assert "Trace32 remote API loaded" in caplog.text
        assert (
            f"ITF connected on {lauterbach_flasher.node}:{lauterbach_flasher.port}"
            in caplog.text
        )


@pytest.mark.parametrize(
    "side_effect_load_library, side_effect_subprocess, expected_log",
    [
        (Exception, None, "Unable to open Trace32"),
        (None, Exception, "Unable to open Trace32"),
        (None, None, "Unable to connect on port"),
    ],
)
def test_open_fail(
    caplog,
    lauterbach_flasher,
    mocker,
    side_effect_load_library,
    side_effect_subprocess,
    expected_log,
):
    mocker.patch("test_flash_lauterbach.StubTrace32Api.T32_Init", return_value=1)
    mocker.patch("ctypes.cdll.LoadLibrary", side_effect=side_effect_load_library)
    mocker.patch("subprocess.Popen", side_effect=side_effect_subprocess)
    lauterbach_flasher.loadup_wait_time = 0

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception) as e:
            lauterbach_flasher.open()
        assert expected_log in caplog.text


def test_close(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api
):

    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()

    with caplog.at_level(logging.INTERNAL_DEBUG):
        lauterbach_flasher.close()

    assert "Disconnect from Trace32 with state 0" in caplog.text


def test_close_wait_raise_except(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api, mocker
):
    mocker.patch(
        "test_flash_lauterbach.StubProcess.wait",
        return_value=2,
        side_effect=subprocess.TimeoutExpired("t32", 5),
    )
    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()
    lauterbach_flasher.close()

    assert "Disconnect from Trace32 with state 0" in caplog.text
    assert "Trace32 failed to exit properly" in caplog.text


def test_flash(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api, mocker
):
    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()
    mocker.patch.object(ctypes, "byref", return_value=CtypeTypeMock(0))
    mocker.patch.object(ctypes, "c_int", return_value=CtypeTypeMock(0))
    mocker.patch("time.sleep", return_value=None)

    with caplog.at_level(logging.INTERNAL_INFO):
        lauterbach_flasher.flash()

    assert "flash procedure successful" in caplog.text


@pytest.mark.parametrize(
    "return_value_t32_cmd, expected_log",
    [
        (-3, "TRACE32 Remote API communication error"),
        (3, "An error occurred during flash,state :"),
    ],
)
def test_flash_exception(
    lauterbach_flasher,
    mock_psutil,
    mock_subprocess,
    mock_remote_api,
    mocker,
    return_value_t32_cmd,
    expected_log,
):
    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()
    mocker.patch.object(ctypes, "byref", return_value=CtypeTypeMock(0))
    mocker.patch.object(ctypes, "c_int", return_value=CtypeTypeMock(0))
    mocker.patch.object(StubTrace32Api, "T32_Cmd", return_value=return_value_t32_cmd)
    mocker.patch.object(StubTrace32Api, "T32_GetMessage", return_value=-3)

    mocker.patch("time.sleep", return_value=None)

    with pytest.raises(Exception) as e:
        lauterbach_flasher.flash()

    assert expected_log in str(e.value)


def test_script_execution_error(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api, mocker
):
    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()
    mocker.patch.object(ctypes, "byref", return_value=CtypeTypeMock(1))
    mocker.patch.object(ctypes, "c_int", return_value=CtypeTypeMock(1))
    mocker.patch("time.sleep", return_value=None)

    with pytest.raises(RuntimeError) as execinfo:
        lauterbach_flasher.flash()

    assert "Error during lauterbach" in str(execinfo.value)
