##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Auxiliary Interface Definition
******************************

:module: auxiliary

:synopsis: Implementation of basic auxiliary functionality and
    definition of abstract methods for override

.. currentmodule:: pykiso


"""

import abc
import logging
import queue
import threading
import time
from typing import Any, List, Optional

from pykiso.test_setup.dynamic_loader import PACKAGE

from .types import MsgType

log = logging.getLogger(__name__)


# Ensure lock and queue unique reference: needed because python will do
# a copy of the created object when the unittests are called
class AuxiliaryInterface(threading.Thread, metaclass=abc.ABCMeta):
    """Defines the Interface of Auxiliaries.

    Auxiliaries get configured by the Test Coordinator, get instantiated by
    the TestCases and in turn use Connectors.
    """

    def __init__(
        self,
        name: str = None,
        is_proxy_capable: bool = False,
        is_pausable: bool = False,
        activate_log: List[str] = None,
    ):
        """Auxiliary thread initialization.

        :param name: alias of the auxiliary instance
        :param is_proxy_capable: notify if the current auxiliary could
            be (or not) associated to a proxy-auxiliary.
        :param is_pausable: notify if the current auxiliary could be
            (or not) paused
        :param activate_log: loggers to deactivate
        """
        # Initialize thread class
        super().__init__()
        self.initialize_loggers(activate_log)
        # Save the name
        self.name = name
        # Define thread control attributes & methods
        self.lock = threading.RLock()
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        self.stop_event = threading.Event()
        self.wait_event = threading.Event()
        self.is_proxy_capable = is_proxy_capable
        self.is_pausable = is_pausable
        # Create state
        self.is_instance = False
        # Start thread
        self.start()

    @staticmethod
    def initialize_loggers(loggers: Optional[List[str]]):
        """Deactivate all external loggers except the specified ones.

        :param loggers: list of logger names to keep activated
        """
        if loggers is None:
            loggers = list()
        # keyword 'all' should keep all loggers to the configured level
        if "all" in loggers:
            log.warning(
                "All loggers are activated, this could lead to performance issues."
            )
            return
        # keep package and auxiliary loggers
        relevant_loggers = {
            name: logger
            for name, logger in logging.root.manager.loggerDict.items()
            if not (name.startswith(PACKAGE) or name.endswith("auxiliary"))
            and not isinstance(logger, logging.PlaceHolder)
        }
        # keep child loggers
        childs = [
            logger
            for logger in relevant_loggers.keys()
            for parent in loggers
            if (logger.startswith(parent) or parent.startswith(logger))
        ]
        loggers += childs
        # keep original level for specified loggers
        loggers_to_deactivate = set(relevant_loggers) - set(loggers)
        for logger_name in loggers_to_deactivate:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    def __repr__(self):
        name = self.name
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def lock_it(self, timeout_in_s: float) -> bool:
        """Lock to ensure exclusivity.

        :param timeout_in_s: How many second you want to wait for the lock
        :type timeout_in_s: integer

        :return: True - Lock done / False - Lock failed
        """
        return self.lock.acquire(timeout=timeout_in_s)

    def unlock_it(self) -> None:
        """Unlock exclusivity"""
        self.lock.release()

    def resume(self) -> None:
        """Resume current auxiliary's run."""
        if not self.stop_event.is_set() and not self.is_instance:
            self.create_instance()
        else:
            log.error("Cannot resume auxiliary, error occurred during creation")

    def suspend(self) -> None:
        """Supend current auxiliary's run."""
        if self.is_instance:
            self.delete_instance()
        else:
            log.error("Cannot suspend auxiliary, error occurred during creation")

    def create_instance(self) -> bool:
        """Create an auxiliary instance and ensure the communication to it.

        :return: message.Message() - Contain received message
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("create_auxiliary_instance")
            # Wait until the request was processed
            report = self.queue_out.get()
            # Release the above lock
            self.lock.release()
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

    def run_command(
        self,
        cmd_message: MsgType,
        cmd_data: Any = None,
        blocking: bool = True,
        timeout_in_s: int = 0,
    ) -> bool:
        """Send a test request.

        :param cmd_message: command request to the auxiliary
        :param cmd_data: data you would like to populate the command with
        :param blocking: If you want the command request to be blocking or not
        :param timeout_in_s: Number of time (in s) you want to wait for an answer

        :return: True - Successfully sent / False - Failed by sending / None
        """
        return_code = False

        log.debug(f"sending command '{cmd_message}' in {self}")
        if cmd_data:
            log.debug(f"command payload data: {repr(cmd_data)}")

        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put(("command", cmd_message, cmd_data))
            log.debug(f"sent command '{cmd_message}' in {self}")
            # Wait until the test request was received
            try:
                log.debug(f"waiting for reply to command '{cmd_message}' in {self}")
                return_code = self.queue_out.get(blocking, timeout_in_s)
                log.debug(
                    f"reply to command '{cmd_message}' received: '{return_code}' in {self}"
                )
            except queue.Empty:
                log.debug("no reply received within time")
            # Release the above lock
            self.lock.release()
            # Return the ack_report if exists
        return return_code

    def wait_and_get_report(
        self, blocking: bool = False, timeout_in_s: int = 0
    ) -> MsgType:
        """Wait for the report of the previous sent test request.

        :param blocking: True: wait for timeout to expire, False: return immediately
        :param timeout_in_s: if blocking, wait the defined time in seconds

        :return: a message.Message() - Message received / None - nothing received
        """
        try:
            return self.queue_out.get(blocking, timeout_in_s)
        except queue.Empty:
            return None

    def abort_command(self, blocking: bool = True, timeout_in_s: float = 25) -> bool:
        """Force test to abort.

        :param blocking: If you want the command request to be blocking or not
        :param timeout_in_s: Number of time (in s) you want to wait
            for an answer

        :return: True - Abort was a success / False - if not
        """
        return_code = False

        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("abort")
            # Wait until the test request was received
            try:
                return_code = self.queue_out.get(blocking, timeout_in_s)
            except queue.Empty:
                log.info("no reply received within time")
            # Release the above lock
            self.lock.release()
            # Return the ack_report if exists
        return return_code

    def stop(self) -> None:
        """Force the thread to stop itself."""
        self.stop_event.set()

    def run(self) -> None:
        """ Run function of the auxiliary thread."""
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
                log.warning(f"Unknown request '{request}', will not be processed!")
                log.warning(f"Aux status: {self.__dict__}")

            # Step 2: Check if something was received from the aux instance if instance was created
            if self.is_instance and not self.is_pausable:
                received_message = self._receive_message(timeout_in_s=0)
                # If yes, send it via the out queue
                if received_message is not None:
                    self.queue_out.put(received_message)

            # Free up cpu usage when auxiliary is suspended
            if not self.is_instance:
                time.sleep(0.050)

            # If auxiliary instance is created and is pausable
            if self.is_instance and self.is_pausable:
                self.wait_event.wait()
        # Thread stop command was set
        log.info("{} was stopped".format(self))
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
