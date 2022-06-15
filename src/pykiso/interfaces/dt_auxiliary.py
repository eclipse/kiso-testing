##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Double Threaded based Auxiliary Interface
*****************************************

:module: dt_auxiliary

:synopsis: common double threaded based auxiliary interface

.. currentmodule:: dt_auxiliary

"""
import abc
import enum
import logging
import queue
import threading
from enum import Enum, unique
from typing import Any, List

from pykiso import AuxiliaryInterface

from ..exceptions import AuxiliaryCreationError

log = logging.getLogger(__name__)


@unique
class AuxState(Enum):

    CREATE_AUXILIARY = enum.auto()
    DELETE_AUXILIARY = enum.auto()


class DTAuxiliaryInterface:
    def __init__(
        self,
        name: str = None,
        is_proxy_capable: bool = False,
        activate_log: List[str] = None,
        auto_start: bool = True,
    ) -> None:
        """Initialize auxiliary attributes

        :param name: alias of the auxiliary instance
        :param is_proxy_capable: notify if the current auxiliary could
            be (or not) associated to a proxy-auxiliary.
        :param activate_log: loggers to deactivate
        :param auto_start: determine if the auxiliayry is automatically
             started (magic import) or manually (by user)
        """
        self.name = name
        self.is_proxy_capable = is_proxy_capable
        self.auto_start = auto_start
        AuxiliaryInterface.initialize_loggers()
        self.lock = threading.RLock()
        self.stop_tx = threading.Event()
        self.stop_rx = threading.Event()
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        self.recv_timeout = 1

    def run_command(
        self,
        cmd_message: Any,
        cmd_data: Any = None,
        blocking: bool = True,
        timeout_in_s: int = 5,
    ) -> Any:
        """Send a request by transmitting it through queue_in and
        waiting for a response using queue_out.

        :param cmd_message: command request to the auxiliary
        :param cmd_data: data you would like to populate the command
            with
        :param blocking: If you want the command request to be
            blocking or not
        :param timeout_in_s: Number of time (in s) you want to wait
            for an answer

        :return: True if the request is correctly executed otherwise
            False
        """
        with self.lock:
            log.debug(
                f"sending command '{cmd_message}' with payload {cmd_data} using {self.name} aux."
            )
            response_received = None
            self.queue_in.put((cmd_message, cmd_data))
            try:
                response_received = self.queue_out.get(blocking, timeout_in_s)
                log.debug(
                    f"reply to command '{cmd_message}' received: '{response_received}' in {self.name}"
                )
            except queue.Empty:
                log.error(
                    f"no reply received within time for command {cmd_message} for payload {cmd_data} using {self.name} aux."
                )
        return response_received

    def delete_instance(self) -> bool:
        """Stop auxiliary's running tasks and activities.

        :return: True if the auxiliary is deleted otherwise False
        """
        log.info(f"deleting instance of auxiliary {self.name}")

        with self.lock:
            is_deleted = self._delete_auxiliary_instance()

            if not is_deleted:
                log.error("Unexpected error occured during auxiliary instance deletion")

            # stop each auxiliary's tasks
            self._stop_tx_task()
            self._stop_rx_task()

            self.is_instance = False
            return is_deleted

    def create_instance(self) -> bool:
        """Start auxiliary's running tasks and activities.

        :return: True if the auxiliary is created otherwise False

        :raises AuxiliaryCreationError: if instance creation failed
        """
        log.info(f"Creating instance of auxiliary {self.name}")

        with self.lock:
            is_created = self._create_auxiliary_instance()

            if not is_created:
                raise AuxiliaryCreationError(self.name)

            # start each auxiliary's tasks
            self._start_tx_task()
            self._start_rx_task()

            self.is_instance = True
            return is_created

    def _start_tx_task(self) -> None:
        """Start transmission task."""
        log.info(f"start transmit task {self.name}_tx")
        self.tx_thread = threading.Thread(
            name=f"{self.name}_tx", target=self._transmit_task
        )
        self.tx_thread.start()

    def _start_rx_task(self) -> None:
        """Start reception task."""
        log.info(f"start reception task {self.name}_tx")
        self.rx_thread = threading.Thread(
            name=f"{self.name}_rx", target=self._reception_task
        )
        self.rx_thread.start()

    def _stop_tx_task(self) -> None:
        """Stop transmission task."""
        log.debug(f"stop transmit task {self.name}_tx")
        self.run_command(cmd_message=AuxState.DELETE_AUXILIARY)
        self.stop_tx.set()
        self.tx_thread.join()

    def _stop_rx_task(self) -> None:
        """Stop reception task."""
        log.debug(f"stop reception task {self.name}_rx")
        self.stop_rx.set()
        self.rx_thread.join()

    def start(self) -> bool:
        """Force the auxiliary to start all running tasks and
        activities.

        :return: True if the auxiliary is stopped otherwise False
        """
        return self.create_instance()

    def stop(self) -> bool:
        """Force the auxiliary to stop all running tasks and activities.

        :return: True if the auxiliary is stopped otherwise False
        """
        return self.delete_instance()

    def suspend(self) -> None:
        """Supend current auxiliary's run."""
        if self.is_instance:
            self.delete_instance()
        else:
            log.warning(f"Auxiliary '{self.name}' is already stopped")

    def resume(self) -> None:
        """Resume current auxiliary's run.

        .. warning:: due to the usage of create_instance if an issue
            occurred the exception AuxiliaryCreationError is raised.
        """
        if not self.is_instance:
            self.create_instance()
        else:
            log.warning(f"Auxiliary '{self.name}' is already running")

    def _transmit_task(self) -> None:
        """Auxiliary transmission task.

        Simply call the child defined _run_command method and put the
        the returned command state to queue_out.
        """
        while not self.stop_tx.is_set():

            cmd, data = self.queue_in.get()

            # just stop the current Tx thread task when the instance
            # is inteneded to be deleted
            if cmd == AuxState.DELETE_AUXILIARY:
                break

            self._run_command(cmd, data)

    def _reception_task(self) -> None:
        """Auxiliary reception task.

        Simply call the child defined _receive_message method and
        put the received message in the queue_out.
        """
        while not self.stop_rx.is_set():
            self._receive_message(timeout_in_s=self.recv_timeout)

    @abc.abstractmethod
    def _create_auxiliary_instance(self) -> bool:
        """Create the auxiliary instance with witch we will communicate.

        :return: True - Successfully created / False - Failed by creation

        .. note: Errors should be logged via the logging with the right level
        """

    @abc.abstractmethod
    def _delete_auxiliary_instance(self) -> bool:
        """Delete the auxiliary instance with witch we will communicate.

        :return: True - Successfully deleted / False - Failed deleting

        .. note: Errors should be logged via the logging with the right level
        """

    @abc.abstractmethod
    def _run_command(self, cmd_message: Any, cmd_data: bytes = None) -> None:
        """Run a command for the auxiliary.

        :param cmd_message: command to send

        :param cmd_data: payload data for the command
        """

    @abc.abstractmethod
    def _receive_message(self, timeout_in_s: float) -> None:
        """Defines what needs to be done as a receive message. Such as,
            what do I need to do to receive a message.

        :param timeout_in_s: How much time to block on the receive
        """
