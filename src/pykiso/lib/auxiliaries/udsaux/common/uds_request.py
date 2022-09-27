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

.. currentmodule:: uds_request
"""

from enum import Enum


class TupleEnum(tuple, Enum):
    """Base class for creating enumerated constants that are also
    subclasses of tuple.
    """

    pass


class UDSCommands:
    """Generic UDS commands defined by ISO 14229-1."""

    class TesterPresent(TupleEnum):
        """UDS requests to signal to the device that the client is still present"""

        TESTER_PRESENT = (0x3E, 0x00)
        TESTER_PRESENT_NO_RESPONSE = (0x3E, 0x80)

    class ECUReset(TupleEnum):
        """UDS requests to perform reset on components."""

        HARD_RESET = (0x11, 0x01)
        KEY_OFF_ON_RESET = (0x11, 0x02)
        SOFT_RESET = (0x11, 0x03)
        ENABLE_RAPID_POWER_SHUTDOWN = (0x11, 0x04)
        DISABLE_RAPID_POWER_SHUTDOWN = (0x11, 0x05)

    class Session(TupleEnum):
        """UDS requests to perform session change."""

        DEFAULT_SESSION = (0x10, 0x01)
        PROGRAMMING_SESSION = (0x10, 0x02)
        EXTENDED_SESSION = (0x10, 0x03)
        SAFTEFY_SYSTEM_SESSION = (0x10, 0x04)
