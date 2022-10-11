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
from typing import IO, ByteString, Callable, Dict, List, Optional, Tuple, Union

from pykiso import Message
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


class ProcessExit:
    ...


# Marker for process exit in queue_in
PROCESS_EXIT = ProcessExit()


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
        self.process: Optional[subprocess.Popen] = None
        self.queue_in: Optional[queue.Queue[Union[ProcessMessage, ProcessExit]]] = None
        self.stdout_thread: Optional[threading.Thread] = None
        self.stderr_thread: Optional[threading.Thread] = None
        self.lock: threading.Lock = threading.Lock()
        # Counter for finished threads
        self.ready: int = 0
        # Buffer for messages that where read from the process but not yet returned by _cc_receive
        self.buffer: List[Union[ProcessMessage, ProcessExit]] = []

    def start(self, executable: Optional[str] = None, args: Optional[List[str]] = None):
        """Start a process

        :param executable: The executable path. Default to path specified in yaml if not given.
        :param args: The process arguments. Default to arguments specified in yaml if not given.

        :raises CCProcessError: Process is already running
        """
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
            self.stdout_thread = self._start_read_thread(self.process.stdout, "stdout")
        if self.pipe_stderr:
            self.stderr_thread = self._start_read_thread(self.process.stderr, "stderr")

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
                if self.text:
                    data = stream.readline()
                else:
                    data = stream.read(1)
                if len(data) == 0:
                    break
                self.queue_in.put(ProcessMessage(name, data))
        finally:
            with self.lock:
                self.ready += 1
                if self.ready == int(self.pipe_stdout) + int(self.pipe_stderr):
                    # PROCESS_EXIT marks the termination of all read threads
                    self.queue_in.put(PROCESS_EXIT)

    def _cc_close(self) -> None:
        """Close the channel."""
        self._cleanup()

    def _cc_send(self, msg: MessageType, raw: bool = False, **kwargs) -> None:
        """Execute process commands or write data to stdin

        :param msg: data to send
        :param raw: unused

        :raises CCProcessError: Stdin pipe is not enabled

        """
        if isinstance(msg, dict) and msg.get("command") == "start":
            self.start(msg.get("executable"), msg.get("args"))
        elif self.pipe_stdin:
            if self.process is None:
                raise CCProcessError("Process is not running.")
            log.internal_debug(f"write stdin: {msg}")
            self.process.stdin.write(msg)
            self.process.stdin.flush()
        else:
            raise CCProcessError("Can not send to stdin because pipe is not enabled.")

    def _cleanup(self) -> None:
        """Cleanup threads and process objects"""
        if self.process is not None:
            # Terminate the process if still running
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                log.internal_warning(
                    f"Process {self.executable} could not be terminated"
                )
                self.process.kill()
        # Wait for the threads to finish
        if self.stdout_thread is not None:
            self.stdout_thread.join()
            self.stdout_thread = None
        if self.stderr_thread is not None:
            self.stderr_thread.join()
            self.stderr_thread = None
        if self.queue_in is not None:
            self.queue_in = None

    def _cc_open(self) -> None:
        """Implement abstract method"""
        pass

    def _read_existing(self) -> Optional[ProcessMessage]:
        """Read buffered messages that where already received from the process.
        Messages from the same stream are combined.
        This is only used in binary mode.

        :return: Existing messages
        """
        messages = self.buffer

        # Get all messages from the process that are available
        while not self.queue_in.empty():
            messages.append(self.queue_in.get_nowait())
        i = 1
        # Find messages from the same stream(first entry in the tuple) as the first message
        while (
            i < len(messages)
            and messages[0] is not PROCESS_EXIT
            and messages[i] is not PROCESS_EXIT
            and messages[0].stream == messages[i].stream
        ):
            i += 1

        # Save the remaining messages for next time
        self.buffer = messages[i:]

        # Process only messages from the same stream
        messages = messages[:i]
        if len(messages) == 0:
            return None

        if messages[0] is PROCESS_EXIT:
            return messages[0]

        # Join messages
        return ProcessMessage(messages[0].stream, b"".join([x.data for x in messages]))

    def _create_message_dict(self, msg: Union[ProcessMessage, ProcessExit]) -> dict:
        """Create a dict from an entry in the process queue

        :param msg: The message to convert

        :return: The dictionary
        """
        if isinstance(msg, ProcessMessage):
            ret = {"msg": {msg.stream: msg.data}}
        elif msg is PROCESS_EXIT:
            ret = {"msg": {"exit": self.process.returncode}}
        return ret

    def _cc_receive(self, timeout: float = 0.0001, raw: bool = False) -> MessageType:
        """Receive messages

        :param timeout: Time to wait in seconds for a message to be received
        :param raw: unused

        return The received message
        """
        if self.queue_in is None:
            return {"msg": None}

        # Get message from the queue
        try:
            read = self.queue_in.get(True, timeout)
        except queue.Empty:
            # Queue is empty, but there might be previously received messages when in binary mode
            existing = None if self.text else self._read_existing()
            if existing is not None:
                ret = self._create_message_dict(existing)
            else:
                ret = {"msg": None}
            return ret

        if read is not PROCESS_EXIT:
            # A message was received
            if self.text:
                # Just return that message when in text mode
                ret = self._create_message_dict(read)
            else:
                # Add message to the buffer and join messages for binary mode
                self.buffer.append(read)
                existing = self._read_existing()
                ret = self._create_message_dict(existing)
            return ret
        else:
            # None is the marker for process finish. Get the exit code.
            self._cleanup()
            return self._create_message_dict(PROCESS_EXIT)
