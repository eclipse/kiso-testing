##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
record auxiliary plugin
***********************

:module: record_auxiliary

:synopsis: implementation of existing RecordAuxiliary for
    Robot framework usage.

.. currentmodule:: record_auxiliary

"""


from robot.api.deco import keyword, library

from ..auxiliaries.record_auxiliary import RecordAuxiliary as RecAux
from .aux_interface import RobotAuxInterface


@library(version="0.1.6")
class RecordAuxiliary(RobotAuxInterface):
    """Robot framework plugin for RecordAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=RecAux)

    @keyword("Clear buffer")
    def clear_buffer(self, aux_alias: str) -> None:
        """Clean the buffer that contain received messages.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.clear_buffer(self)

    @keyword("Stop recording")
    def stop_recording(self, aux_alias: str) -> None:
        """Stop recording by suspending auxiliary.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.stop_recording(self)

    @keyword("Start recording")
    def start_recording(self, aux_alias: str) -> None:
        """Start recording by suspending auxiliary.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.start_recording(self)

    @keyword("Is log empty")
    def is_log_empty(self, aux_alias: str) -> bool:
        """Check if log buffer is not empty.

        :param aux_alias: auxiliary's alias

        :return: True if log is empty, False either
        """
        aux = self._get_aux(aux_alias)
        return aux.is_log_empty(self)

    @keyword("Dump data to file")
    def dump_to_file(self, filename: str, aux_alias: str) -> bool:
        """Write the log buffer content in the given file.

        :param filename: name of the file where data are saved
        :param aux_alias: auxiliary's alias

        :return: True if the dumping has been successful, otherwise
            False
        """
        aux = self._get_aux(aux_alias)
        return aux.dump_to_file(self, filename)

    @keyword("Set data")
    def set_data(self, data: str, aux_alias: str) -> None:
        """Add data to the already existing data string.

        :param data: the data to be write over the existing string
        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.set_data(self)

    @keyword("Get data")
    def get_data(self, aux_alias: str) -> str:
        """Return the entire log buffer content.

        :param aux_alias: auxiliary's alias

        :return: entire log buffer content
        """
        aux = self._get_aux(aux_alias)
        return aux.get_data(self)

    @keyword("New log")
    def new_log(self, aux_alias: str) -> str:
        """Get new entries (after cursor position) from the log. This
        will set the cursor.

        :param aux_alias: auxiliary's alias

        :return: return log after cursor
        """
        aux = self._get_aux(aux_alias)
        return aux.new_log(self)

    @keyword("Previous log")
    def previous_log(self, aux_alias: str) -> str:
        """set cursor position to current position.

        This will also display the logs from the last cursor position
        in the log.

        :param aux_alias: auxiliary's alias

        :return: log from the last current position
        """
        aux = self._get_aux(aux_alias)
        return aux.previous_log(self)

    @keyword("Is message in log")
    def is_message_in_log(
        self,
        aux_alias: str,
        message: str,
        from_cursor: bool = True,
        set_cursor: bool = True,
        display_log: bool = False,
    ) -> bool:
        """Check for a message being in log.

        :param aux_alias: auxiliary's alias
        :param message: str message to check presence in logs.
        :param from_cursor: whether to get the logs from the last cursor
            position (True) or the full logs
        :param set_cursor: whether to update the cursor
        :param display_log: whether to log (via logging) the retrieved
            part or just return it

        :return: True if a message is in log, False else
        """
        aux = self._get_aux(aux_alias)
        return aux.is_message_in_log(self)

    @keyword("Is message in full log")
    def is_message_in_full_log(self, aux_alias: str, message: str) -> bool:
        """Check for a message being in log.

        :param aux_alias: auxiliary's alias
        :param message: message to check presence in logs.

        :return: True if a message is in log, False else
        """
        aux = self._get_aux(aux_alias)
        return aux.is_message_in_full_log(self)

    @keyword("Wait for message in log")
    def wait_for_message_in_log(
        self,
        aux_alias: str,
        message: str,
        timeout: float = 10.0,
        interval: float = 0.1,
        from_cursor: bool = True,
        set_cursor: bool = True,
        display_log: bool = False,
        exception_on_failure: bool = True,
    ) -> bool:
        """Poll log every 100ms and fail if messages has not shown up
        within the specified timeout.

        :param aux_alias: auxiliary's alias
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

        :return: True if the message have been received in the log, False else
        """
        aux = self._get_aux(aux_alias)
        return aux.wait_for_message_in_log(self)
