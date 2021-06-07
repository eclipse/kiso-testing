import ctypes
import logging
import pathlib
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
    with caplog.at_level(logging.DEBUG):
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


def test_open_fail(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api, mocker
):
    mocker.patch("test_flash_lauterbach.StubTrace32Api.T32_Init", return_value=1)
    lauterbach_flasher.loadup_wait_time = 0

    with pytest.raises(Exception) as e:
        lauterbach_flasher.open()
    assert "Unable to connect on port" in str(e.value)


def test_close(
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api
):

    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()

    with caplog.at_level(logging.INFO):
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
    caplog, lauterbach_flasher, mock_psutil, mock_subprocess, mock_remote_api
):

    lauterbach_flasher.loadup_wait_time = 0
    lauterbach_flasher.open()

    with caplog.at_level(logging.INFO):
        lauterbach_flasher.flash()

    assert "flash procedure successful" in caplog.text
