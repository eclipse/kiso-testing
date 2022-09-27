##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Multiprocessing based Auxiliary Interface
*****************************************

:module: mp_auxiliary

:synopsis: common multiprocessing based auxiliary interface

.. currentmodule:: mp_auxiliary

"""

import abc
import logging
import multiprocessing
import time
from typing import List

import pykiso
from pykiso.auxiliary import AuxiliaryCommon

from ..exceptions import AuxiliaryCreationError
from ..types import MsgType

log = logging.getLogger(__name__)


class MpAuxiliaryInterface(multiprocessing.Process, AuxiliaryCommon):
    """Defines the interface of all multiprocessing based auxiliaries.

    Auxiliaries get configured by the Test Coordinator, get instantiated by
    the TestCases and in turn use Connectors.
    """

    def __init__(
        self,
        name: str = None,
        is_proxy_capable: bool = False,
        activate_log: List[str] = None,
    ) -> None:
        """Auxiliary initialization.

        :param name: alias of the auxiliary instance
        :param is_proxy_capable: notify if the current auxiliary could
            be (or not) associated to a proxy-auxiliary.
        :param activate_log: loggers to deactivate
        """
        self.name = name
        # Define process control attributes & methods
        self.lock = multiprocessing.RLock()
        self.queue_in = multiprocessing.Queue()
        self.queue_out = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        self.is_proxy_capable = is_proxy_capable
        self.logger = None
        self.is_instance = False
        # store the logging information
        self._activate_log = activate_log
        self._log_level = pykiso.logging_initializer.get_logging_options().log_level
        self._aux_copy = None
        super().__init__()

    def create_instance(self) -> bool:
        """Create an auxiliary instance and ensure the communication to it.

        :return: verdict on instance creation, True if everything was
            fine otherwise False

        :raises AuxiliaryCreationError: if instance creation failed
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("create_auxiliary_instance")
            # Wait until the request was processed
            self.is_instance = self.queue_out.get()
            # Release the above lock
            self.lock.release()
            # aux instance can't be created just exit
            if not self.is_instance:
                raise AuxiliaryCreationError(self.name)
            # Return the report
            return self.is_instance

    def delete_instance(self) -> bool:
        """Delete an auxiliary instance and its communication to it.

        :return: verdict on instance deletion, False if everything was
            fine otherwise True(instance was not deleted correctly)
        """
        if self.lock.acquire() and self.is_alive():
            # Trigger the internal requests
            self.queue_in.put("delete_auxiliary_instance")
            # Wait until the request was processed
            self.is_instance = self.queue_out.get()
            # Release the above lock
            self.lock.release()
            # Return the report
            return self.is_instance

    def initialize_loggers(self) -> None:
        """Initialize the logging mechanism for the current process."""
        log_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(module)s:%(lineno)d: %(message)s"
        )
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }

        # if logging is not activate take WARNING level otherwise the
        # the specified one
        level = (
            logging.WARNING if self._activate_log is None else levels[self._log_level]
        )

        # init StreamHandler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(log_format)

        # add StreamHandler and level to root logger
        self.logger = multiprocessing.get_logger()
        self.logger.addHandler(stream_handler)
        self.logger.setLevel(logging.DEBUG)

    def run(self) -> None:
        """Run function of the auxiliary process."""
        # initialize logging mechanism at process startup
        self.initialize_loggers()
        while not self.stop_event.is_set():
            # Step 1: Check if a request is available & process it
            request = ""
            # Check if a request was received
            if not self.queue_in.empty():
                request = self.queue_in.get_nowait()
            # Process the request
            if request == "create_auxiliary_instance" and not self.is_instance:
                # Call the internal instance creation method
                self.is_instance = self._create_auxiliary_instance()
                # Enqueue the result for the request caller
                self.queue_out.put(self.is_instance)
            elif request == "delete_auxiliary_instance" and self.is_instance:
                # Call the internal instance delete method
                self.is_instance = not self._delete_auxiliary_instance()
                # Enqueue the result for the request caller
                self.queue_out.put(self.is_instance)
            elif (
                isinstance(request, tuple)
                and self.is_instance
                and request[0] == "command"
            ):
                # If the instance is created, send the requested command
                # to the instance via the internal method
                _, cmd, data = request
                cmd_response = self._run_command(cmd, data)
                if cmd_response is not None:
                    self.queue_out.put(cmd_response)
            elif request == "abort" and self.is_instance:
                self.queue_out.put(self._abort_command())
            elif request != "":
                # A request was received but could not be processed
                self.logger.warning(
                    f"Unknown request '{request}', will not be processed!"
                )

            # Step 2: Check if something was received from the aux instance if instance was created
            if self.is_instance:
                received_message = self._receive_message(timeout_in_s=0)
                # If yes, send it via the out queue
                if received_message is not None:
                    self.queue_out.put(received_message)

            # Free up cpu usage when auxiliary is suspended
            if not self.is_instance:
                time.sleep(0.050)

        # Thread stop command was set
        self.logger.info("{} was stopped".format(self))
        # Delete auxiliary external instance if not done
        if self.is_instance:
            self._delete_auxiliary_instance()

    @abc.abstractmethod
    def _create_auxiliary_instance(self) -> bool:
        """Create the auxiliary instance with witch we will communicate.

        :return: True - Successfully created / False - Failed by creation

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _delete_auxiliary_instance(self) -> bool:
        """Delete the auxiliary instance with witch we will communicate.

        :return: True - Successfully deleted / False - Failed deleting

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _run_command(self, cmd_message: MsgType, cmd_data: bytes = None) -> MsgType:
        """Run a command for the auxiliary.

        :param cmd_message: command in form of a message to run

        :param cmd_data: payload data for the command

        :return: True - Successfully received by the instance / False - Failed sending

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _abort_command(self) -> bool:
        """Abort the sent command."""
        pass

    @abc.abstractmethod
    def _receive_message(self, timeout_in_s: float) -> MsgType:
        """Defines what needs to be done as a receive message. Such as,
            what do I need to do to receive a message.

        :param timeout_in_s: How much time to block on the receive

        :return: message.Message - If one received / None - Else
        """
        pass
