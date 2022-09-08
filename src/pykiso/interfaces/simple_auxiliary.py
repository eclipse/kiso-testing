##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Simple Auxiliary Interface
**************************

:module: simple_auxiliary

:synopsis: common auxiliary interface for very simple auxiliary
    (without usage of thread or multiprocessing)

.. currentmodule:: simple_auxiliary

"""
import abc
import logging
from typing import List, Optional

from ..exceptions import AuxiliaryCreationError
from ..logging_initializer import add_logging_level, initialize_loggers
from .thread_auxiliary import AuxiliaryInterface

log = logging.getLogger(__name__)


class SimpleAuxiliaryInterface(metaclass=abc.ABCMeta):
    """Define the interface for all simple auxiliary where usage of
    thread or mulitprocessing is not necessary.
    """

    def __new__(cls, *args, **kwargs):
        """Create instance and add internal kiso log levels in
        case the auxiliary is used outside the pykiso context
        """
        if not hasattr(logging, "INTERNAL_WARNING"):
            add_logging_level("INTERNAL_WARNING", logging.WARNING + 1)
            add_logging_level("INTERNAL_INFO", logging.INFO + 1)
            add_logging_level("INTERNAL_DEBUG", logging.DEBUG + 1)
        return super(SimpleAuxiliaryInterface, cls).__new__(cls)

    def __init__(self, name: str = None, activate_log: List[str] = None) -> None:
        """Auxiliary initialization.

        :param activate_log: loggers to deactivate
        :param name: alias of the auxiliary instance
        """
        self.name = name
        self.is_instance = False
        initialize_loggers(activate_log)

    def __repr__(self) -> str:
        name = self.name if self.name is not None else ""
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def create_instance(self) -> bool:
        """Create an auxiliary instance and ensure the communication to it.

        :return: True if creation was successful otherwise False

        :raises AuxiliaryCreationError: if instance creation failed
        """
        self.is_instance = self._create_auxiliary_instance()
        if not self.is_instance:
            raise AuxiliaryCreationError(self.name)
        return self.is_instance

    def delete_instance(self) -> bool:
        """Delete an auxiliary instance and its communication to it.

        :return: True if deletion was successful otherwise False
        """
        report = self._delete_auxiliary_instance()
        self.is_instance = not report
        return report

    def resume(self) -> None:
        """Resume current auxiliary's run, by running the
        create_instance method in the background.

        .. warning:: due to the usage of create_instance if an issue
            occurred the exception AuxiliaryCreationError is raised.
        """
        if not self.is_instance:
            self.create_instance()
        else:
            log.internal_warning(f"Auxiliary '{self}' is already running")

    def suspend(self) -> None:
        """Suspend current auxiliary's run."""
        if self.is_instance:
            self.delete_instance()
        else:
            log.internal_warning(f"Auxiliary '{self}' is already stopped")

    def stop(self):
        """Stop the auxiliary"""
        self._delete_auxiliary_instance()

    @abc.abstractmethod
    def _create_auxiliary_instance(self) -> bool:
        """Create the auxiliary instance with which we will communicate.

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
