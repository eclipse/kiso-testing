##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


"""
uds_request
***********

:module: uds_request

:synopsis: This module contains basics commands functions enums.

.. currentmodule:: util_request
"""

from enum import Enum


class ListEnum(list, Enum):
    """Base class for creating enumerated constants that are also
    subclasses of list.
    """

    pass


class UDSCommands:
    """UDS mainstream command"""

    class ECUReset(ListEnum):
        """UDS requests to perform reset on components."""

        ECU_RESET_SW_INSTALLATION_STATE = [0x11, 0x01]
        FORCE_ECU_RESET = [0x11, 0x02]
        SOFT_RESET = [0x11, 0x03]
        SHUTDOWN = [0x11, 0x06]

    class Session(ListEnum):
        """UDS requests to perform session change."""

        DEFAULT_SESSION = [0x10, 0x01]
        PROGRAMMING_SESSION = [0x10, 0x02]
        EXTENDED_SESSION = [0x10, 0x03]
        PROTECTED_SESSION = [0x10, 0x40]
