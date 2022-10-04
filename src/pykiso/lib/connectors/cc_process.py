##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Process Channel
*************

:module: cc_process

:synopsis: CChannel implementation for process execution.

The CCProcess channel provides functionality to start a process and
to communicate with it.

.. currentmodule:: cc_process

"""

import logging
import queue
import subprocess
import threading
from typing import IO, ByteString, Callable, Dict, List, Optional, Union

from pykiso import Message
from pykiso.connector import CChannel

log = logging.getLogger(__name__)

MessageType = Union[str, ByteString]


class CCProcessError(BaseException):
    ...


class CCProcess(CChannel):
    def __init__(
        self,
        shell: bool = False,
        pipe_stderr: bool = False,
        pipe_stdout: bool = True,
        pipe_stdin: bool = False,
        text: bool = True,
        cwd: Optional[str] = None,
        env: Optional[str] = None,
        encoding: Optional[str] = None,
        executable: Optional[str] = None,
        args: List[str] = [],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.shell = shell
        self.pipe_stderr = pipe_stderr
        self.pipe_stdout = pipe_stdout
        self.pipe_stdin = pipe_stdin
        self.encoding = encoding
        self.executable = executable
        self.args = args
        self.text = text
        self.cwd = cwd
        self.env = env
        self.process = None
        self.queue_in = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.lock = threading.Lock()
        self.ready = 0
        self.buffer = []

    def _cc_open(self) -> None:
        pass

    def start(self, executable: Optional[str] = None, args: Optional[List[str]] = None):
        if self.process is not None and self.process.returncode is None:
            raise CCProcessError(f"Process is already running: {self.executable}")

        self._cleanup()
        self.ready = 0
        self.queue_in = queue.Queue()

        self.process = subprocess.Popen(
            ([executable] if executable is not None else [self.executable])
            + (args if args is not None else self.args),
            stderr=subprocess.PIPE if self.pipe_stderr else None,
            stdout=subprocess.PIPE if self.pipe_stdout else None,
            stdin=subprocess.PIPE if self.pipe_stdin else None,
            shell=self.shell,
            text=self.text,
            encoding=self.encoding,
            cwd=self.cwd,
            env=self.env,
        )

        if self.pipe_stdout:
            self.stdout_thread = self._start_task(self.process.stdout, "stdout")
        if self.pipe_stderr:
            self.stderr_thread = self._start_task(self.process.stderr, "stderr")

    def _start_task(self, stream: IO, name: str) -> threading.Thread:
        thread = threading.Thread(
            name=f"cc_process_{name}", target=self._read_thread, args=(stream, name)
        )
        thread.start()
        return thread

    def _read_thread(self, stream: IO, name: str) -> None:
        try:
            while True:
                if self.text:
                    data = stream.readline()
                else:
                    data = stream.read(1)
                if len(data) == 0:
                    break
                # print(data)
                self.queue_in.put((name, data))
        finally:
            with self.lock:
                self.ready += 1
                if self.ready == int(self.pipe_stdout) + int(self.pipe_stderr):
                    # None marks the termination of all read threads
                    self.queue_in.put(None)

    def _cc_close(self) -> None:
        if self.process is not None:
            self.process.terminate()
        self._cleanup()

    def _cc_send(self, msg: MessageType, raw: bool = False, **kwargs) -> None:
        if isinstance(msg, dict) and "command" in msg:
            if msg["command"] == "start":
                self.start(msg["executable"], msg["args"])
        elif self.pipe_stdin:
            log.debug(f"write stdin: {msg}")
            self.process.stdin.write(msg)
            self.process.stdin.flush()
        else:
            raise CCProcessError("Can not send to stdin because pipe is not enabled.")

    def _cleanup(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
        if self.stdout_thread is not None:
            self.stdout_thread.join()
            self.stdout_thread = None
        if self.stderr_thread is not None:
            self.stderr_thread.join()
            self.stderr_thread = None
        if self.queue_in is not None:
            self.queue_in = None

    def stream_name(self, msg):
        if "stdout" in msg:
            return "stdout"
        if "stdin" in msg:
            return "stdin"
        return None

    def read_existing(self):
        messages = self.buffer
        while not self.queue_in.empty():
            messages.append(self.queue_in.get_nowait())
        i = 1
        while (
            i < len(messages)
            and messages[0] is not None
            and messages[i] is not None
            and messages[0][0] == messages[i][0]
        ):
            print(i)
            i += 1

        self.buffer = messages[i:]

        messages = messages[:i]
        if len(messages) == 0:
            return []
        # if len(messages) == 1:
        #    return [messages[0]]
        r = [(messages[0][0], b"".join([x[1] for x in messages]))]
        print(f"XXX {r}")
        return r

    def _cc_receive(self, timeout: float = 0.0001, raw: bool = False) -> MessageType:
        if self.queue_in is None:
            r = {"msg": None}
            print(f"process: {r}")
            return {"msg": None}

        try:
            read = self.queue_in.get(True, timeout)
        except queue.Empty:
            existing = [] if self.text else self.read_existing()
            print(f"existing: {existing}")
            if len(existing) > 0:
                r = {"msg": {existing[0][0]: existing[0][1]}}
            else:
                r = {"msg": None}
            print(f"process: {r}")
            return r

        if read is not None:
            if self.text:
                r = {"msg": {read[0]: read[1]}}
            else:
                self.buffer.append(read)
                existing = self.read_existing()
                print(f"existing: {existing}")
                r = {"msg": {existing[0][0]: existing[0][1]}}
                print(f"process: {r}")
            return r
        else:
            self._cleanup()
            r = {"msg": {"exit": self.process.returncode}}
            print(f"process: {r}")
            return {"msg": {"exit": self.process.returncode}}
