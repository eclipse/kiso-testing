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
import functools
import logging
import queue
import threading
import warnings
from typing import Any, Callable, List, Optional

from ..auxiliary import AuxCommand, AuxiliaryInterface, close_connector, flash_target, open_connector
from ..exceptions import AuxiliaryCreationError, AuxiliaryNotStarted
from ..logging_initializer import add_internal_log_levels, initialize_loggers

log = logging.getLogger(__name__)


class DTAuxiliaryInterface(AuxiliaryInterface):
    def __init__(
        self,
        name: str = None,
        is_proxy_capable: bool = False,
        connector_required: bool = True,
        activate_log: List[str] = None,
        tx_task_on=True,
        rx_task_on=True,
        auto_start: bool = True,
    ) -> None:
        super().__init__(
            name,
            is_proxy_capable,
            connector_required,
            activate_log,
            tx_task_on,
            rx_task_on,
            auto_start,
        )
        warnings.warn(
            "The DTAuxiliaryInterface is deprecated and has been renamed to AuxiliaryInterface. Please use AuxiliaryInterface instead.",
            category=FutureWarning,
        )
