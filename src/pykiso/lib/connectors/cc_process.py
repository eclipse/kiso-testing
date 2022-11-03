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
***************

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
from dataclasses import dataclass
from typing import IO, ByteString, List, Optional, Union

from pykiso.connector import CChannel

log = logging.getLogger(__name__)

MessageType = Union[str, ByteString]


class CCProcessError(BaseException):
    ...


@dataclass
class ProcessMessage:
    """Holds the data that is read from the process"""

    # Stream name: stdout or stderr
    stream: str
    # Data as bytes or string
    data: Union[str, bytes]


@dataclass
class ProcessExit:
    """Contains information about process exit"""

    exit_code: int


class CCProcess(CChannel):
    """Channel to run processes"""

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
        """Initialize a process

        :param shell: Start process through shell
        :param pipe_stderr: Pipe stderr for reading with this connector
        :param pipe_stdout: Pipe stdout for reading with this connector
        :param pipe_stdin:  Pipe stdin for writing with this connector
        :param text: Read/write stdout, stdin, stderr in binary mode
        :param cwd: The current working directory for the new process
        :param env: Environment variables for the new process
        :param encoding: Encoding to use in text mode
        :param executable: The path of the executable for the process
        :param args: Process arguments

        """
        super().__init__(**kwargs)
        self._shell = shell
        self._pipe_stderr = pipe_stderr
        self._pipe_stdout = pipe_stdout
        self._pipe_stdin = pipe_stdin
        self._encoding = encoding
        self._executable = executable
        self._args = args
        self._text = text
        self._cwd = cwd
        self._env = env
        self._process: Optional[subprocess.Popen] = None
        self._queue_in: Optional[queue.Queue[Union[ProcessMessage, ProcessExit]]] = None
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._finished_threads_count = 0
        # Buffer for messages that where read from the process but not yet returned by _cc_receive
        self._buffer: List[Union[ProcessMessage, ProcessExit]] = []

    def start(self, executable: Optional[str] = None, args: Optional[List[str]] = None):
        """Start a process

        :param executable: The executable path. Default to path specified in yaml if not given.
        :param args: The process arguments. Default to arguments specified in yaml if not given.

        :raises CCProcessError: Process is already running
        """
        if self._process is not None and self._process.returncode is None:
            raise CCProcessError(f"Process is already running: {self._executable}")

        self._cleanup()
        self._finished_threads_count = 0
        self._queue_in = queue.Queue()

        self._process = subprocess.Popen(
            ([executable] if executable is not None else [self._executable])
            + (args if args is not None else self._args),
            stderr=subprocess.PIPE if self._pipe_stderr else None,
            stdout=subprocess.PIPE if self._pipe_stdout else None,
            stdin=subprocess.PIPE if self._pipe_stdin else None,
            shell=self._shell,
            text=self._text,
            encoding=self._encoding,
            cwd=self._cwd,
            env=self._env,
        )

        if self._pipe_stdout:
            self._stdout_thread = self._start_read_thread(
                self._process.stdout, "stdout"
            )
        if self._pipe_stderr:
            self._stderr_thread = self._start_read_thread(
                self._process.stderr, "stderr"
            )

    def _start_read_thread(self, stream: IO, name: str) -> threading.Thread:
        """Start a read thread

        :param stream: The stream to read from
        :param name: The name of the stream

        :return: The thread object
        """
        thread = threading.Thread(
            name=f"cc_process_{name}", target=self._read_thread, args=(stream, name)
        )
        thread.start()
        return thread

    def _read_thread(self, stream: IO, name: str) -> None:
        """Thread for reading data from stdout or stderr

        :param stream: The stream to read from
        :param name: The name of the stream
        """
        try:
            while True:
                if self._text:
                    data = stream.readline()
                else:
                    data = stream.read(1)
                if len(data) == 0:
                    break
                self._queue_in.put(ProcessMessage(name, data))
        finally:
            with self._lock:
                self._finished_threads_count += 1
                if self._finished_threads_count == int(self._pipe_stdout) + int(
                    self._pipe_stderr
                ):
                    # ProcessExit marks the termination of all read threads
                    self._queue_in.put(ProcessExit(self._process.wait()))

    def _cc_close(self) -> None:
        """Close the channel."""
        self._cleanup()

    def _cc_send(self, msg: MessageType, **kwargs) -> None:
        """Execute process commands or write data to stdin

        :param msg: data to send

        :raises CCProcessError: Stdin pipe is not enabled

        """
        if isinstance(msg, dict) and msg.get("command") == "start":
            self.start(msg.get("executable"), msg.get("args"))
        elif self._pipe_stdin:
            if self._process is None:
                raise CCProcessError("Process is not running.")
            log.internal_debug(f"write stdin: {msg}")
            self._process.stdin.write(msg)
            self._process.stdin.flush()
        else:
            raise CCProcessError("Can not send to stdin because pipe is not enabled.")

    def _cleanup(self) -> None:
        """Cleanup threads and process objects"""
        if self._process is not None:
            # Terminate the process if still running
            self._process.terminate()
            try:
                self._process.wait(5)
            except subprocess.TimeoutExpired:
                log.internal_warning(
                    f"Process {self._executable} could not be terminated"
                )
                self._process.kill()
        # Wait for the threads to finish
        if self._stdout_thread is not None:
            self._stdout_thread.join()
            self._stdout_thread = None
        if self._stderr_thread is not None:
            self._stderr_thread.join()
            self._stderr_thread = None
        if self._queue_in is not None:
            self._queue_in = None

    def _cc_open(self) -> None:
        """Implement abstract method"""
        pass

    def _read_existing(self) -> Optional[ProcessMessage]:
        """Read buffered messages that where already received from the process.
        Messages from the same stream are combined.
        This is only used in binary mode.

        :return: Existing messages
        """
        messages = self._buffer

        # Get all messages from the process that are available
        while not self._queue_in.empty():
            messages.append(self._queue_in.get_nowait())
        i = 1
        # Find messages from the same stream(first entry in the tuple) as the first message
        while (
            i < len(messages)
            and not isinstance(messages[0], ProcessExit)
            and not isinstance(messages[i], ProcessExit)
            and messages[0].stream == messages[i].stream
        ):
            i += 1

        # Save the remaining messages for next time
        messages, self._buffer = messages[:i], messages[i:]

        # Process only messages from the same stream
        messages = messages[:i]
        if len(messages) == 0:
            return None

        if isinstance(messages[0], ProcessExit):
            return messages[0]

        # Join messages
        return ProcessMessage(messages[0].stream, b"".join([x.data for x in messages]))

    @staticmethod
    def _create_message_dict(msg: Union[ProcessMessage, ProcessExit]) -> dict:
        """Create a dict from an entry in the process queue

        :param msg: The message to convert

        :return: The dictionary
        """
        if isinstance(msg, ProcessMessage):
            ret = {"msg": {msg.stream: msg.data}}
        elif isinstance(msg, ProcessExit):
            ret = {"msg": {"exit": msg.exit_code}}
        return ret

    def _cc_receive(self, timeout: float = 0.0001) -> MessageType:
        """Receive messages

        :param timeout: Time to wait in seconds for a message to be received
        :param size: unused

        return The received message
        """
        if self._queue_in is None:
            return {"msg": None}

        # Get message from the queue
        try:
            read = self._queue_in.get(True, timeout)
        except queue.Empty:
            # Queue is empty, but there might be previously received messages when in binary mode
            existing = None if self._text else self._read_existing()
            if existing is not None:
                ret = CCProcess._create_message_dict(existing)
            else:
                ret = {"msg": None}
            return ret

        if not isinstance(read, ProcessExit):
            # A message was received
            if self._text:
                # Just return that message when in text mode
                ret = CCProcess._create_message_dict(read)
            else:
                # Add message to the buffer and join messages for binary mode
                self._buffer.append(read)
                existing = self._read_existing()
                ret = CCProcess._create_message_dict(existing)
            return ret
        else:
            # Process has exited
            self._cleanup()
            return CCProcess._create_message_dict(read)
