"""
Auxiliary Interface Definition
******************************

:module: auxiliary

:synopsis: Implementation of basic auxiliary functionality and definition of abstract methods for override

.. currentmodule:: pykiso

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

"""

import threading
import queue
import logging
import abc

from pykiso import message
from pykiso.types import MsgType

# Ensure lock and queue unique reference: needed because python will do a copy of the created object when the unittests are called


class AuxiliaryInterface(threading.Thread, metaclass=abc.ABCMeta):
    """ Defines the Interface of Auxiliaries

    Auxiliaries get configured by the Test Coordinator, get instantiated by
    the TestCases and in turn use Connectors.
    """

    def __init__(self, name: str = None):
        """ Auxiliary thread initialization

        :param name: alias of the auxiliary instance
        """
        # Initialize thread class
        super(AuxiliaryInterface, self).__init__()
        self.name = name
        # Save the name
        # Define thread control attributes & methods
        self.lock = threading.RLock()
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        self.stop_event = threading.Event()
        # Create state
        self.is_instance = False
        # Start thread
        self.start()

    def __repr__(self):
        name = self.name
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def lock_it(self, timeout_in_s):
        """ Lock to ensure exclusivity

        :param timeout_in_s: How many second you want to wait for the lock
        :type timeout_in_s: integer

        :return: True - Lock done / False - Lock failed
        """
        return self.lock.acquire(timeout=timeout_in_s)

    def unlock_it(self):
        """ Unlock exclusivity
        """
        self.lock.release()

    def create_instance(self):
        """ Create an auxiliary instance and ensure the communication to it

        :return: message.Message() - Contain received message
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("create_auxiliary_instance")
            # Wait until the request was processed
            report = self.queue_out.get()  # TODO add try & except?
            # Release the above lock
            self.lock.release()
            # Return the report
            return report

    def delete_instance(self):
        """ Delete an auxiliary instance and its communication to it

        :return: message.Message() - Contain received message
        """
        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put("delete_auxiliary_instance")
            # Wait until the request was processed TODO add try & except?
            report = self.queue_out.get()
            # Release the above lock
            self.lock.release()
            # Return the report
            return report

    def run_command(
        self,
        cmd_message: MsgType,
        cmd_data: bytes = None,
        blocking: bool = True,
        timeout_in_s: float = 0,
    ) -> bool:
        """ Send a test request

        :param cmd_message: command request to the auxiliary

        :param cmd_data: data you would like to populate the command with

        :param blocking: If you want the command request to be blocking or not

        :param timeout_in_s: Number of time (in s) you want to wait for an answer

        :return: True - Successfully sent / False - Failed by sending / None
        """
        # TODO is bytes the correct datatype for cmd_data?
        return_code = False
        logging.info(f"sending command '{cmd_message}' in {self}")
        if cmd_data:
            logging.info(f"command payload data: {repr(cmd_data)}")

        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put(("command", cmd_message, cmd_data))
            logging.debug(f"sent command '{cmd_message}' in {self}")
            # Wait until the test request was received
            try:
                logging.debug(f"waiting for reply to command '{cmd_message}' in {self}")
                return_code = self.queue_out.get(blocking, timeout_in_s)
                logging.debug(
                    f"reply to command '{cmd_message}' received: '{return_code}' in {self}"
                )
            except queue.Empty:
                logging.debug(f"no reply received within time")
            # Release the above lock
            self.lock.release()
            # Return the ack_report if exists
        return return_code

    def wait_and_get_report(
        self, blocking: bool = False, timeout_in_s: float = 0
    ) -> MsgType:
        """ Wait for the report of the previous sent test request

        :param blocking: True: wait for timeout to expire, False: return immediately
        :param timeout_in_s: if blocking, wait the defined time in seconds

        :return: a message.Message() - Message received / None - nothing received
        """
        try:
            return self.queue_out.get(blocking, timeout_in_s)
        except queue.Empty:
            pass

    def abort_command(self) -> bool:
        """ Force test to abort

        :return: True - Abort was a success / False - if not # TODO maybe use the signal lib for the abort?
        """
        report = None
        logging.info("abort waited at {}".format(self))
        if self.lock.acquire():
            # Abort what is currently running in the task
            report = self._abort_command()
            # Release the above lock
            self.lock.release()
            # Return the report
        return report

    def stop(self):
        """ Force the thread to stop itself
        """
        self.stop_event.set()

    def run(self):
        """ Run function of the auxiliary thread """
        while not self.stop_event.is_set():
            # Step 1: Check if a request is available & process it
            request = ""
            # Check if a request was recieved
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
                # If the instance is created, send the requested command to the instance via the internal method
                _, cmd, data = request
                self.queue_out.put(self._run_command(cmd, data))
            elif request != "":
                # A request was received but could not be processed
                logging.warning(f"Unknown request '{request}', will not be processed!")
                logging.warning(f"Aux status: {self.__dict__}")

            # Step 2: Check if something was received from the aux instance if instance was created
            if self.is_instance:
                received_message = self._receive_message(timeout_in_s=0)
                # If yes, send it via the out queue
                if received_message is not None:
                    self.queue_out.put(received_message)
        # Thread stop command was set
        logging.info("{} was stopped".format(self))
        # Delete auxiliary external instance if not done
        if self.is_instance:
            self._delete_auxiliary_instance()

    @abc.abstractmethod
    def _create_auxiliary_instance(self) -> bool:
        """ Create the auxiliary instance with witch we will communicate

        :return: True - Successfully created / False - Failed by creation

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _delete_auxiliary_instance(self) -> bool:
        """ Delete the auxiliary instance with witch we will communicate

        :return: True - Successfully deleted / False - Failed deleting

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _run_command(self, cmd_message: MsgType, cmd_data: bytes = None) -> bool:
        """ Run a command for the auxiliary

        :param cmd_message: command in form of a message to run

        :param cmd_data: payload data for the command

        :return: True - Successfully received bv the instance / False - Failed sending

        .. note: Errors should be logged via the logging with the right level
        """
        pass

    @abc.abstractmethod
    def _abort_command(self):
        """ Abort the sent command
        """
        pass

    @abc.abstractmethod
    def _receive_message(self, timeout_in_s: float):
        """ Defines what needs to be done as a receive message. Such as, what do I need to do to receive a message

        :param timeout_in_s: How much time to block on the receive

        :return: message.Message - If one received / None - Else
        """
        pass
