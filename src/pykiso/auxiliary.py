##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
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
from __future__ import annotations

import abc
import logging
import queue
import time
from typing import Any

from pykiso.logging_initializer import add_internal_log_levels
from pykiso.test_setup.config_registry import ConfigRegistry
from pykiso.types import MsgType

log = logging.getLogger(__name__)


class AuxiliaryCommon(metaclass=abc.ABCMeta):
    """Class use to encapsulate all common methods/attributes for both
    multiprocessing and thread auxiliary interface.
    """

    def __init__(self) -> None:
        """Auxiliary common attributes initialization."""
        add_internal_log_levels()
        self.name = None
        self.queue_in = None
        self.lock = None
        self.queue_out = None
        self.is_instance = False
        self.stop_event = None
        self._aux_copy = None
        self.connector_required = True

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

    def create_copy(self, *args, **config: dict) -> AuxiliaryCommon:
        """Create a copy of the actual auxiliary instance with the
        new desired configuration.

        .. note:: only named arguments have to be used

        .. warning:: the call of create_copy will automatically suspend
            the current auxiliary until the it copy is destroyed

        :param config: new desired auxiliary configuration

        :return: a brand new auxiliary instance

        :raises Exception: if positional parameters is given or unknown
            named parameters are given
        """
        # only named parameters are allowed
        if args:
            raise Exception("Only use named parameters when invoking create_copy")
        # if a copy already exist return the actual one
        if self._aux_copy is not None:
            log.internal_warning(
                f"A copy of {self} already exists, destroy it before creating a new one"
            )
            return self._aux_copy
        # get modified parameters based on the yaml one
        base_conf = modified_conf = ConfigRegistry.get_aux_config(self.name)
        modified_params = list(set(config) & set(base_conf))
        added_params = list(set(config) - set(base_conf))
        if self.is_alive():
            self.suspend()
            # add this timeout if cc_proxy connectors are used (avoid
            # possible ConnectionRefusedError)
            time.sleep(1.100)
        # apply new configuration parameters values based on yaml config
        for name, val in base_conf.items():
            if name in modified_params:
                modified_conf[name] = config[name]
        # add new parameters values (not explicitly mention in yaml)
        for name in added_params:
            modified_conf[name] = config[name]
        try:
            # create a brand new auxiliary instance
            self._aux_copy = self.__class__(**modified_conf)
        except TypeError:
            raise Exception(
                f"Unknown parameter(s) given to {self.name} see {added_params}"
            )
        self._aux_copy.name = self.name
        auto_start = getattr(self._aux_copy, "auto_start", None)
        if auto_start:
            self._aux_copy.start()
            self._aux_copy.create_instance()
        return self._aux_copy

    def destroy_copy(self) -> None:
        """Stop the current auxiliary copy and resume the original.

        .. warning:: stop the copy auxiliary will automatically start
            the base/original one
        """
        if self._aux_copy is not None:
            # delete and stop the thread properly
            self._aux_copy.delete_instance()
            self._aux_copy.stop()
            self._aux_copy.join()
            self._aux_copy = None
        if not self.is_alive():
            self.start()
        if not self.is_instance:
            self.resume()

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

        log.internal_debug(f"sending command '{cmd_message}' in {self}")
        if cmd_data:
            log.internal_debug(f"command payload data: {repr(cmd_data)}")

        if self.lock.acquire():
            # Trigger the internal requests
            self.queue_in.put(("command", cmd_message, cmd_data))
            log.internal_debug(f"sent command '{cmd_message}' in {self}")
            # Wait until the test request was received
            try:
                log.internal_debug(
                    f"waiting for reply to command '{cmd_message}' in {self}"
                )
                return_code = self.queue_out.get(blocking, timeout_in_s)
                log.internal_debug(
                    f"reply to command '{cmd_message}' received: '{return_code}' in {self}"
                )
            except queue.Empty:
                log.internal_debug("no reply received within time")
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
                log.internal_info("no reply received within time")
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
        if self._aux_copy is not None:
            # if an auxiliary copy remains just stop it before the
            # original one
            self._aux_copy.delete_instance()
            self._aux_copy.stop()
            self._aux_copy.join()
            self._aux_copy = None
        self.stop_event.set()

    def resume(self) -> None:
        """Resume current auxiliary's run, by running the
        create_instance method in the background.

        .. warning:: due to the usage of create_instance if an issue
            occurred the exception AuxiliaryCreationError is raised.
        """
        if not self.stop_event.is_set() and not self.is_instance:
            self.create_instance()
        else:
            log.internal_warning(f"Auxiliary '{self}' is already running")

    def suspend(self) -> None:
        """Supend current auxiliary's run."""
        if self.is_instance:
            self.delete_instance()
        else:
            log.internal_warning(f"Auxiliary '{self}' is already stopped")

    @abc.abstractmethod
    def create_instance(self) -> bool:
        """Handle auxiliary creation."""
        pass

    @abc.abstractmethod
    def delete_instance(self) -> bool:
        """Handle auxiliary deletion."""
        pass

    @abc.abstractmethod
    def run(self) -> None:
        """Run function of the auxiliary."""
        pass
