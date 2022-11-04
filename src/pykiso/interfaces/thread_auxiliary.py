##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Thread based Auxiliary Interface
********************************

:module: thread_auxiliary

:synopsis: common thread based auxiliary interface

.. currentmodule:: thread_auxiliary

.. warning :: AuxiliaryInterface will be deprecated in a few releases!

"""
import abc
import logging
import queue
import threading
import time
import warnings
from typing import List

from pykiso.auxiliary import AuxiliaryCommon

from ..exceptions import AuxiliaryCreationError
from ..logging_initializer import initialize_loggers
from ..types import MsgType

log = logging.getLogger(__name__)


# Ensure lock and queue unique reference: needed because python will do
# a copy of the created object when the unittests are called
class AuxiliaryInterface(threading.Thread, AuxiliaryCommon):
    """Defines the Interface of all thread based auxiliaries.

    Auxiliaries get configured by the Test Coordinator, get instantiated by
    the TestCases and in turn use Connectors.
    """

    def __init__(
        self,
        name: str = None,
        is_proxy_capable: bool = False,
        activate_log: List[str] = None,
        auto_start: bool = True,
    ) -> None:
        """Auxiliary initialization.

        :param name: alias of the auxiliary instance
        :param is_proxy_capable: notify if the current auxiliary could
            be (or not) associated to a proxy-auxiliary.
        :param activate_log: loggers to deactivate
        :param auto_start: determine if the auxiliayry is automatically
             started (magic import) or manually (by user)
        """
        # Initialize thread class
        super().__init__()
        initialize_loggers(activate_log)
        # Save the name
        self.name = name
        # Define thread control attributes & methods
        self.lock = threading.RLock()
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        self.stop_event = threading.Event()
        self.is_proxy_capable = is_proxy_capable
        # Create state
        self.is_instance = False
        self.auto_start = auto_start
        self._aux_copy = None

        warnings.warn(
            "AuxiliaryInterface will be deprecated in a few releases!",
            category=FutureWarning,
        )

    def start(self) -> None:
        """Start the thread and create the auxiliary only if auto_start
        flag is False.
        """
        if not self.is_alive():
            super().start()
            if not self.auto_start:
                self.create_instance()

    def create_instance(self) -> bool:
        """Create an auxiliary instance and ensure the communication to it.

        :return: message.Message() - Contain received message

        :raises AuxiliaryCreationError: if instance creation failed
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("create_auxiliary_instance")
            # Wait until the request was processed
            report = self.queue_out.get()
            # Release the above lock
            self.lock.release()
            # aux instance can't be created just exit
            if not report:
                raise AuxiliaryCreationError(self.name)
            # Return the report
            return report

    def delete_instance(self) -> bool:
        """Delete an auxiliary instance and its communication to it.

        :return: message.Message() - Contain received message
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("delete_auxiliary_instance")
            # Wait until the request was processed
            report = self.queue_out.get()
            # Release the above lock
            self.lock.release()
            # Return the report
            return report

    def run(self) -> None:
        """Run function of the auxiliary thread."""
        while not self.stop_event.is_set():
            # Step 1: Check if a request is available & process it
            request = ""
            # Check if a request was received
            if not self.queue_in.empty():
                request = self.queue_in.get_nowait()
            # Process the request
            if request == "create_auxiliary_instance" and not self.is_instance:
                # Call the internal instance creation method
                return_code = self._create_auxiliary_instance()
                # Based on the result set status:
                self.is_instance = return_code
                # Enqueue the result for the request caller
                self.queue_out.put(return_code)
            elif request == "delete_auxiliary_instance" and self.is_instance:
                # Call the internal instance delete method
                return_code = self._delete_auxiliary_instance()
                # Based on the result set status:
                self.is_instance = not return_code
                # Enqueue the result for the request caller
                self.queue_out.put(return_code)
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
                log.internal_warning(
                    f"Unknown request '{request}', will not be processed!"
                )
                log.internal_warning(f"Aux status: {self.__dict__}")

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
        log.internal_info("{} was stopped".format(self))
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
