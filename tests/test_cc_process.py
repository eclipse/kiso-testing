import sys
from pathlib import Path

import pytest

executable = str(Path(sys.executable).resolve())
from pykiso.lib.connectors.cc_process import CCProcess


def test_constructor(mocker):

    popen_mock = mocker.patch("subprocess.Popen")

    cc_process = CCProcess()


def test_send(mocker):

    popen_mock = mocker.patch("subprocess.Popen")

    cc_process = CCProcess()

    # cc_process._cc_send({"msg":{"command":"start"}})
    cc_process._cc_send({"command": "start", "executable": "exe", "args": ["1", "2"]})
    assert cc_process.process is not None


# def test_receive(mocker):

#     popen_mock = mocker.patch("subprocess.Popen")

#     cc_process = CCProcess()
#     cc_process._cc_send({"command": "start", "executable": "exe", "args": ["1", "2"]})

#     cc_process.process.stdout.readline.return_value = [b"1", b"234"]
#     x = cc_process._cc_receive()
#     cc_process.process.stdout.readline.assert_called_once()
#     assert x == {"msg": {"data": [b"1", b"234"]}}


def test_process(mocker):

    cc_process = CCProcess(
        shell=False,
        pipe_stderr=True,
        pipe_stdout=True,
        pipe_stdin=True,
        executable=executable,
        args=[
            "-c",
            'import sys;import time;print(sys.stdin.readline());sys.stdout.flush();time.sleep(1);print(\'error\', file=sys.stderr);sys.stderr.flush();time.sleep(1);print("hello");print("pykiso")',
        ],
    )
    cc_process.start()
    """cc_process.cc_send(
        {
            "command": "start",
            "executable": executable,
            "args": [
                "-c",
                'import sys;import time;print(sys.stdin.readline());sys.stdout.flush();time.sleep(1);print(\'error\', file=sys.stderr);sys.stderr.flush();time.sleep(1);print("hello");print("pykiso")',
            ],
        }
    )"""
    cc_process._cc_send("hi\r\n")
    # cc_process.start()
    assert cc_process._cc_receive(3) == "hi"
    assert cc_process.cc_receive(3) == {"msg": {"stderr": "error\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": "hello\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": "pykiso\n"}}
    cc_process.cc_receive(3)
    cc_process._cc_close()
    cc_process.cc_receive(3)
