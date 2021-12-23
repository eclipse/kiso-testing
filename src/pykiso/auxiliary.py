##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Auxiliary common Interface Definition
*************************************

:module: auxiliary

:synopsis: base auxiliary interface

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


class AuxiliaryCommon(metaclass=abc.ABCMeta):
    """Class use to encapsulate all common methods/attributes for both
    multiprocessing and thread auxiliary interface.
    """

    def __init__(self) -> None:
        """Auxiliary common attributes initialization."""
        self.name = None
        self.queue_in = None
        self.lock = None
        self.queue_out = None
        self.is_instance = False
        self.stop_event = None

    def __repr__(self) -> str:
        name = self.name
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def lock_it(self, timeout_in_s: float) -> bool:
        """Lock to ensure exclusivity.

        :param timeout_in_s: How many second you want to wait for the lock

        :return: True - Lock done / False - Lock failed
        """
        return self.lock.acquire(timeout=timeout_in_s)

    def unlock_it(self) -> None:
        """Unlock exclusivity"""
        self.lock.release()

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

    def stop(self) -> None:
        """Force the thread to stop itself."""
        self.stop_event.set()

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

    @abc.abstractmethod
    def create_instance(self) -> bool:
        """Run function of the auxiliary."""
        pass

    @abc.abstractmethod
    def delete_instance(self) -> bool:
        """Run function of the auxiliary."""
        pass

    @abc.abstractmethod
    def run(self) -> None:
        """Run function of the auxiliary."""
        pass
