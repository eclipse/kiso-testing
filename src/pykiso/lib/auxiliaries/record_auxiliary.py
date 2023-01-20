##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Record Auxiliary
****************

:module: record_auxiliary

:synopsis: Auxiliary used to record a connectors receive channel.

.. currentmodule:: record_auxiliary

"""

import io
import logging
import multiprocessing
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pykiso import CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)

log = logging.getLogger(__name__)


class StringIOHandler(io.StringIO):
    def __init__(self, multiprocess: bool = False) -> None:
        """Constructor

        :param multiprocess: use a thread or multiprocessing lock.
        """
        super(StringIOHandler, self).__init__()
        if multiprocess:
            self.data_lock = multiprocessing.Lock()
        else:
            self.data_lock = threading.Lock()

    def get_data(self) -> str:
        """Get data from the string

        :return: data from the string
        """
        with self.data_lock:
            return self.getvalue()

    def set_data(self, data: str) -> None:
        """Add data to the already existing data string

        :param data: the data to be write over the existing string
        """
        with self.data_lock:
            self.write(data)


class RecordAuxiliary(DTAuxiliaryInterface):
    """Auxiliary used to record a connectors receive channel."""

    LOG_HEADER = "Received data :"

    def __init__(
        self,
        com: CChannel,
        is_active: bool = False,
        timeout: float = 0,
        log_folder_path: str = "",
        max_file_size: int = int(5e7),
        multiprocess: bool = False,
        manual_start_record: bool = False,
        **kwargs,
    ) -> None:
        """Constructor.

        :param com: Communication connector to record
        :param is_active: Flag to actively poll receive channel in
            another thread
        :param timeout: timeout for the receive channel
        :param log_path: path to the log folder
        :param max_file_size: maximal size of the data string
        :param multiprocess: use a Process instead of a Thread for
            active polling.
            Note1: the data will automatically be saved
            Note2: if proxy usage, all connectors should be 'CCMpProxy'
                and 'processing' flag set to True
        :param manual_start_record: flag to not start recording on
            auxiliary creation
        """
        super().__init__(
            is_proxy_capable=True, tx_task_on=False, rx_task_on=False, **kwargs
        )
        self.channel = com
        self.is_active = is_active
        self.timeout = timeout
        self.stop_receive_event = None
        self._receive_thread_or_process = None
        self.multiprocess = multiprocess
        self.cursor = 0
        self.log_folder_path = log_folder_path
        self._data = StringIOHandler(multiprocess)
        self.max_file_size = max_file_size

        if self.is_active and not manual_start_record:
            self.start_recording()

        if self.multiprocess:
            log.internal_warning(
                "Logs will only be dumped into a file due due to the multiprocess flag"
            )

    def get_data(self) -> str:
        """Return the entire log buffer content.

        :return: buffer content
        """
        data = self._data.get_data()
        return data

    def set_data(self, data: str) -> None:
        """Add data to the already existing data string.

        :param data: the data to be write over the existing string
        """
        self._data.set_data(data)

    def _create_auxiliary_instance(self) -> bool:
        """Open the connector and start running receive thread
        if is_active is set.

        :return: True if successful
        """

        log.internal_info("Create auxiliary instance")
        log.internal_info("Enable channel")

        try:
            if not self.is_active:
                self.channel.open()
        except Exception:
            log.exception("Error encountered during channel creation.")
            return False
        return True

    def _delete_auxiliary_instance(self) -> bool:
        """Close connector and stop receive thread when is_active flag
        is set.

        :return: always True
        """
        log.internal_info("Delete auxiliary instance")

        self.stop_recording()

        try:
            if not self.is_active:
                self.channel.close()
        except Exception:
            log.exception("Unable to close Channel.")

        return True

    def receive(self) -> None:
        """Open channel and actively poll the connectors receive channel.
        Stop and close connector when stop receive event has been set.
        """
        try:
            self.channel.open()
        except Exception:
            log.exception("Error encountered while channel creation.")
            return

        log.internal_info(f"Received message/log at {self.log_folder_path}")
        self._data.write(self.LOG_HEADER)
        while not self.stop_receive_event.is_set():
            if sys.getsizeof(self.get_data()) > self.max_file_size:
                log.error("Data size too large")

            recv_response = self.channel.cc_receive(timeout=self.timeout)

            stream = recv_response.get("msg")
            source = recv_response.get("remote_id")

            if stream:
                stream = self.parse_bytes(stream)
                if source is not None:
                    self.set_data(f"\n{source}    {stream}")
                else:
                    self.set_data("\n" + stream)

        if self.multiprocess:
            # dump data inside the process
            self.dump_to_file(f"record_{type(self.channel).__name__}.log")

        try:
            self.channel.close()
        except Exception:
            log.exception("Error encountered while closing channel.")

    @staticmethod
    def parse_bytes(data: bytes) -> str:
        """Decode the received bytes

        :param data: data to be decoded

        :return: data decoded
        """
        # decode
        try:
            return data.decode()
        except UnicodeDecodeError:
            pass
        # get Hex values
        try:
            return data.hex()
        except Exception:
            pass

        # Fail decoding, parse RAW data in string (avoid losing it)
        log.error(f"Could not parse the received data: {data}")
        return str(data)

    def clear_buffer(self) -> None:
        """Clean the buffer that contain received messages."""
        log.internal_info("Clearing buffer")
        self._data = StringIOHandler(self.multiprocess)
        self.cursor = 0

    def stop_recording(self) -> None:
        """Stop recording."""
        if (
            self._receive_thread_or_process is not None
            and self._receive_thread_or_process.is_alive()
        ):
            self.stop_receive_event.set()
            self._receive_thread_or_process.join()
            log.internal_info(f"{self.name} Recording has stopped")
        else:
            log.internal_info("Already Stopped")

    def start_recording(self) -> None:
        """Clear buffer and start recording."""
        # Ensure no record is on-going
        if (
            self._receive_thread_or_process is None
            or not self._receive_thread_or_process.is_alive()
        ):
            # define multiprocessing or Thread variables
            if self.multiprocess:
                self.stop_receive_event = multiprocessing.Event()
                self._receive_thread_or_process = multiprocessing.Process(
                    target=self.receive
                )
            else:
                self.stop_receive_event = threading.Event()
                self._receive_thread_or_process = threading.Thread(target=self.receive)

            self.clear_buffer()
            self._receive_thread_or_process.start()
            log.internal_info(f"{self.name} Recording has started")
        else:
            log.internal_info(f"{self.name} Already started")

    def is_log_empty(self) -> bool:
        """Check if logs are available in the log buffer.

        :return: True if log is empty, False either
        """
        return len(self.get_data()) - len(self.LOG_HEADER) <= 0

    def dump_to_file(self, filename: str, mode: str = "w+", data: str = None) -> bool:
        """Writing data in file.

        :param filename: name of the file where data are saved
        :param mode: modes of opening a file (eg: w, a)
        :param data: Optional write/append specific data to the file.

        :return: True if the dumping has been successful, False else

        :raises FileNotFoundError: if the given folder path is not a
            folder
        """
        # check if there are data
        if (data is None and self.is_log_empty()) or data == "":
            log.internal_warning("Log data is empty. skip dump to file.")
            return False

        path_to_file = Path(self.log_folder_path) / filename
        path_to_file.parent.mkdir(parents=True, exist_ok=True)

        with open(path_to_file, mode) as f:
            f.write(data or self.get_data())
            log.internal_info(f"Log written in {path_to_file}.")

        return True

    def search_regex_in_folder(self, regex: str) -> Optional[Dict[str, List[str]]]:
        """Returns all occurrences found by the regex in the logs and
        message received.

        :param regex: str regex to compare to logs

        :return: dictionary with filename and the list of matches with
            regular expression

        :raises FileNotFoundError: if the given folder path is not a
            folder
        """

        regex_in_folder = {}
        log_folder_path = Path(self.log_folder_path)
        if not log_folder_path.is_dir():
            log.error(f"folder {self.log_folder_path} does not exist")
            raise FileNotFoundError(f"Path {log_folder_path} does not exist.")

        for file in log_folder_path.iterdir():
            file_path = log_folder_path / file
            log_file_content = file_path.read_text()
            list_regex_in_file = re.findall(regex, log_file_content, re.MULTILINE)
            regex_in_folder[str(file)] = list_regex_in_file

        return regex_in_folder

    def search_regex_in_file(self, regex: str, filename: str) -> Optional[List[str]]:
        """Returns all occurrences found by the regex in the logs and
        message received.

        :param regex: str regex to compare to logs
        :param filename: filename of the desired file

        :return: list of matches with regular expression in the chosen
            file
        """
        path = Path(self.log_folder_path) / filename
        if not path.exists():
            log.error(f"No such file {path}")
            return None

        log_file_content = path.read_text()
        list_regex_in_file = re.findall(regex, log_file_content, re.MULTILINE)

        return list_regex_in_file

    def search_regex_current_string(self, regex: str) -> Optional[List[str]]:
        """Returns all occurrences found by the regex in the logs and
            message received.

        :param regex: str regex to compare to logs

        :return: list of matches with regular expression in the current
            string
        """
        list_regex_in_string = re.findall(regex, self.get_data(), re.MULTILINE)
        return list_regex_in_string

    def _log_query(
        self,
        from_cursor: bool = True,
        set_cursor: bool = True,
        display_log: bool = False,
    ) -> str:
        """Provide the internal log interaction mechanism.

        :param from_cursor: whether to get the logs from the last cursor
            position (True) or the full logs
        :param set_cursor: whether to update the cursor to the last
            position of the string
        :param display_log: whether to log (via logging) the retrieved
            part or just return it

        :return: string with concerned log(s)
        """
        output = self.get_data()
        end = len(output)
        start = min(self.cursor, end)
        if from_cursor:
            output = output[start:]
        if set_cursor:
            self.cursor = end
        if display_log and output:
            logging.info(output)
        return output

    def previous_log(self) -> str:
        """set cursor position to current position.

        This will also display the logs from the last cursor position
        in the log.

        :return: log from the last current position
        """
        return self._log_query(from_cursor=True, set_cursor=False, display_log=False)

    def new_log(self) -> str:
        """Get new entries (after cursor position) from the log. This will set the cursor.

        :return: return log after cursor
        """
        return self._log_query(from_cursor=True, set_cursor=True, display_log=False)

    def is_message_in_log(
        self,
        message: str,
        from_cursor: bool = True,
        set_cursor: bool = True,
        display_log: bool = False,
    ) -> bool:
        """Check for a message being in log.

        :param message: str message to check presence in logs.
        :param from_cursor: whether to get the logs from the last cursor
            position (True) or the full logs
        :param set_cursor: whether to update the cursor
        :param display_log: whether to log (via logging) the retrieved
            part or just return it

        :return: True if a message is in log, False otherwise.
        """
        ret_logs = self._log_query(
            from_cursor=from_cursor, set_cursor=set_cursor, display_log=display_log
        )

        return message in ret_logs

    def is_message_in_full_log(self, message: str):
        """Check for a message being in log.

        :param message: message to check presence in logs.
        :return: True if a message is in log, False otherwise
        """
        ret_logs = self.get_data()
        return message in ret_logs

    def wait_for_message_in_log(
        self,
        message: str,
        timeout: float = 10.0,
        interval: float = 0.1,
        from_cursor: bool = True,
        set_cursor: bool = True,
        display_log: bool = False,
        exception_on_failure: bool = True,
    ) -> bool:
        """Poll log at every interval time, fail if messages has not
        shown up within the specified timeout and exception set to True,
        log an error otherwise.

        :param message: str message expected to show up
        :param timeout: int timeout in seconds for the check
        :param interval: int period in seconds for the log poll
        :param from_cursor: whether to get the logs from the last cursor
            position (True) or the full logs
        :param set_cursor: whether to update the cursor to the last log
            position
        :param display_log: whether to log (via logging) the retrieved
            part or just return it
        :param exception_on_failure: if set, raise a TimeoutError if the
            expected messages wasn't found in the logs. Otherwise,
            simply output a warning.

        :return: True if the message have been received in the log,
            False otherwise

        :raises TimeoutError: when a given message has not arrived in
            time
        """
        start = time.time()
        while not self.is_message_in_log(
            message,
            from_cursor=from_cursor,
            set_cursor=set_cursor,
            display_log=display_log,
        ):
            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                if exception_on_failure:
                    raise TimeoutError(
                        f"Maximum wait time for message {message} "
                        f"in log exceeded (waited {elapsed_time:.1f}s)."
                    )
                else:
                    logging.warning(
                        f"Maximum wait time for message {message} "
                        f"in log exceeded (waited {elapsed_time:.1f}s)."
                    )
                    return False
            time.sleep(interval)
        logging.info(f"Received message after {(time.time() - start):.1f}s")
        return True

    def _run_command(self, cmd_message: Any, cmd_data: Optional[bytes]) -> None:
        """Not used.

        Simply respect the interface.
        """

    def _receive_message(self, timeout_in_s: float) -> None:
        """Not used.

        Simply respect the interface.
        """
