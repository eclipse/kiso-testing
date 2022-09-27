##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
uds_response
************

:module: uds_response

:synopsis: This module contains an enum listing the
    UDS negative response codes and a wrapper around
    raw UDS responses.

.. currentmodule:: uds_response
"""
import logging
from collections import UserList
from enum import IntEnum
from typing import List

log = logging.getLogger(__name__)


class UdsResponse(UserList):
    """List wrapper adding attributes relative to a UDS response."""

    NEGATIVE_RESPONSE_SID = 0x7F

    def __init__(self, response_data: List[int]) -> None:
        """Initialize attributes.

        :param response_data: the original response data.
        """
        super().__init__(response_data)
        self.is_negative = False
        self.nrc = None
        if self.data and self.data[0] == self.NEGATIVE_RESPONSE_SID:
            self.is_negative = True
            self.nrc = NegativeResponseCode(self.data[2])

    def __repr__(self):
        if self.data:
            return "0x" + bytes(self.data).hex().upper()
        else:
            return "No data."


class NegativeResponseCode(IntEnum):
    """NRC code response"""

    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INVALID_FORMAT = 0x13
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUB_NET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION = 0x26
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    INVALID_KEY = 0x35
    EXCEED_NUMBER_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78

    @classmethod
    def _missing_(cls, value: int) -> int:
        """Instead of raising a ValueError on a missing member,
        create a NRC UNKNOWN and return it.

        :param value: missing NRC value.
        :return: a new NRC member UNKNOWN with the missing value.
        """
        log.internal_warning(f"Unknown NRC: {value}")
        new_member = int.__new__(cls, value)
        new_member._name_ = "UNKNOWN"
        new_member._value_ = value
        return new_member
