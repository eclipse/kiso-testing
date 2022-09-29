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
from typing import ByteString, Callable, Dict, List, Optional, Union

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

    def _start_task(self, stream, name) -> threading.Thread:
        thread = threading.Thread(
            name=f"cc_process_{name}", target=self._read_thread, args=(stream, name)
        )
        thread.start()
        return thread

    def _read_thread(self, stream, name) -> None:
        try:
            while True:
                line = stream.readline()
                if len(line) == 0:
                    break
                log.debug(f"read {name}: {line}")
                self.queue_in.put((name, line))
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

    def _cc_receive(self, timeout: float = 0.0001, raw: bool = False) -> MessageType:
        if self.queue_in is None:
            return {"msg": None}

        try:
            read = self.queue_in.get(True, timeout)
        except queue.Empty:
            return {"msg": None}

        if read:
            return {"msg": {read[0]: read[1]}}
        else:
            self._cleanup()
            return {"msg": {"exit": self.process.returncode}}
