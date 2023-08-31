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

    def __init__(
        self,
        response_data: List[int],
        resp_time: float = None,
        pending_resp_times: List[float] = None,
    ) -> None:
        """Initialize attributes.

        :param response_data: the original response data.
        :param resp_time: time to get the response in seconds
        :param pending_resp_times: list of the times between each response pending, in seconds
        """
        super().__init__(response_data)
        self.is_negative = False
        self.nrc = None
        if self.data and self.data[0] == self.NEGATIVE_RESPONSE_SID:
            self.is_negative = True
            self.nrc = NegativeResponseCode(self.data[2])
        self.resp_time = resp_time
        self.pending_resp_times = pending_resp_times

    def __repr__(self):
        if self.data:
            if self.is_negative:
                return f"NegativeUdsResponse({bytes(self.data).hex(sep=' ')}, nrc={self.nrc.name})"
            return f"{self.__class__.__name__}({bytes(self.data).hex(sep=' ')})"
        else:
            return f"{self.__class__.__name__} no data."


class NegativeResponseCode(IntEnum):
    """NRC code response"""

    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INVALID_FORMAT = 0x13
    RESPONSE_TOO_LONG = 0x14
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUB_NET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION = 0x26
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    AUTHENTICATION_REQUIRED = 0x34
    INVALID_KEY = 0x35
    EXCEED_NUMBER_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    SECURE_DATA_TRANSMISSION_REQUIRED = 0x38
    SECURE_DATA_TRANSMISSION_NOT_ALLOWED = 0x39
    SECURE_DATA_VERIFICATION_FAILED = 0x3A
    CERTIFICATE_VERIFICATION_FAILED_INVALID_TIME_PERIODE = 0x50
    CERTIFICATE_VERIFICATION_FAILED_INVALID_SIGNATURE = 0x51
    CERTIFICATE_VERIFICATION_FAILED_INVALID_CHAIN_OF_TRUST = 0x52
    CERTIFICATE_VERIFICATION_FAILED_INVALID_TYPE = 0x53
    CERTIFICATE_VERIFICATION_FAILED_INVALID_FORMAT = 0x54
    CERTIFICATE_VERIFICATION_FAILED_INVALID_CONTENT = 0x55
    CERTIFICATE_VERIFICATION_FAILED_INVALID_SCOPE = 0x56
    CERTIFICATE_VERIFICATION_FAILED_INVALID_CERTIFICATE_REVOKED = 0x57
    OWNERSHIP_VERIFICATION_FAILED = 0x58
    CHALLENGE_CALCULATION_FAILED = 0x59
    SETTING_ACCESS_RIGHT_FAILED = 0x5A
    SESSION_KEY_CREATION_DERIVATION_FAILED = 0x5B
    CONFIGURATION_DATA_USAGE_FAILED = 0x5C
    DE_AUTHENTICATION_FAILED = 0x5D
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    SUBFUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F
    RPM_TOO_HIGH = 0x81
    RPM_TOO_LOW = 0x82
    ENGINE_IS_RUNNING = 0x83
    ENGINE_IS_NOT_RUNNING = 0x84
    ENGINE_TIME_TOO_LOW = 0x85
    TEMPERATURE_TOO_HIGH = 0x86
    TEMPERATURE_TOO_LOW = 0x87
    VEHICULE_SPEED_TOO_HIGH = 0x88
    VEHICULE_SPEED_TOO_LOW = 0x89
    THROTTLE_PEDAL_TOO_LOW = 0x8A
    THROTTLE_PEDAL_TOO_HIGH = 0x8B
    TRANSMISSION_RANGE_NOT_IN_NEUTRAL = 0x8C
    TRANSMISSION_RANGE_NOT_IN_GEAR = 0x8D
    BREAK_SWITCH_NOT_CLOSED = 0x8F
    SHIFTER_LEVER_NOT_IN_PARK = 0x90
    TORQUE_CONVERTER_CLUTCH_LOCKED = 0x91
    VOLTAGE_TOO_HIGH = 0x92
    VOLTAGE_TOO_LOW = 0x93
    RESSOURCE_TEMPORARLY_NOT_AVAILABLE = 0x94

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
