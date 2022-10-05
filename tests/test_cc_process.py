##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys
from pathlib import Path

import pytest

from pykiso.lib.connectors.cc_process import CCProcess, CCProcessError


def test_process(mocker):
    """Test most of the CCProcess functionality with a real process with text output"""

    # Get the path of the python executable to start a python process
    executable = str(Path(sys.executable).resolve())

    cc_process = CCProcess(
        shell=False,
        pipe_stderr=True,
        pipe_stdout=True,
        pipe_stdin=True,
        text=True,
        executable=executable,
        args=[
            "-c",
            # process:
            # read line from stdin and write to stdout
            # sleep 1s
            # print "error" on stderr
            # sleep 1s
            # print "hello" on stdout
            # print "pykiso" on stdout
            'import sys;import time;print(sys.stdin.readline().strip());sys.stdout.flush();time.sleep(1);print(\'error\', file=sys.stderr);sys.stderr.flush();time.sleep(1);print("hello");print("pykiso")',
        ],
    )
    # Start the process
    cc_process.start()
    # Second start raises an exception because the process is already running
    with pytest.raises(CCProcessError):
        cc_process.start()

    # Receive nothing as process waits for input
    assert cc_process.cc_receive(3) == {"msg": None}
    cc_process._cc_send("hi\r\n")
    assert cc_process.cc_receive(3) == {"msg": {"stdout": "hi\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"stderr": "error\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": "hello\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": "pykiso\n"}}
    assert cc_process.cc_receive(3) == {"msg": {"exit": 0}}
    cc_process._cc_close()
    assert cc_process.cc_receive(3) == {"msg": None}


def test_process_binary(mocker):
    """Test most of the CCProcess functionality with a real process with binary output"""

    # Get the path of the python executable to start a python process
    executable = str(Path(sys.executable).resolve())

    cc_process = CCProcess(
        shell=False,
        pipe_stderr=True,
        pipe_stdout=True,
        pipe_stdin=True,
        text=False,
        executable=executable,
        args=[
            "-c",
            # process:
            # read line from stdin and write to stdout
            # sleep 1s
            # print "error" on stderr
            # sleep 1s
            # print "hello" on stdout
            # sleep 1s
            # print "pykiso" on stdout
            'import sys;import time;sys.stdout.write(sys.stdin.readline().strip());sys.stdout.flush();time.sleep(1);sys.stderr.write("error");sys.stderr.flush();time.sleep(1);sys.stdout.write("hello");sys.stdout.flush();time.sleep(1);sys.stdout.write("pykiso")',
        ],
    )
    # Start the process
    cc_process.start()
    # Second start raises an exception because the process is already running
    with pytest.raises(CCProcessError):
        cc_process._cc_send({"command": "start", "executable": "", "args": ""})

    cc_process._cc_send(b"hi\n")
    assert cc_process.cc_receive(3) == {"msg": {"stdout": b"hi"}}
    assert cc_process.cc_receive(3) == {"msg": {"stderr": b"error"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": b"hello"}}
    assert cc_process.cc_receive(3) == {"msg": {"stdout": b"pykiso"}}
    assert cc_process.cc_receive(3) == {"msg": {"exit": 0}}
    cc_process._cc_close()
    assert cc_process.cc_receive(3) == {"msg": None}


def test_send_without_pipe_exception(mocker):
    """Test most of the CCProcess functionality with a real process with text output"""

    cc_process = CCProcess(
        shell=False,
        pipe_stderr=True,
        pipe_stdout=True,
        pipe_stdin=False,
        text=False,
    )

    with pytest.raises(CCProcessError):
        cc_process._cc_send("hi")


def test_send_without_process(mocker):
    """Test most of the CCProcess functionality with a real process with text output"""

    cc_process = CCProcess(
        shell=False,
        pipe_stderr=True,
        pipe_stdout=True,
        pipe_stdin=True,
        text=False,
    )

    with pytest.raises(CCProcessError):
        cc_process._cc_send("hi")
