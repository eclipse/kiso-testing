##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS-specific Exceptions
***********************

:module: uds_exceptions

:synopsis: Exceptions to be raised in UDS

.. currentmodule:: uds_exceptions

"""


class UDSError(Exception):
    def __init__(self):
        self.msg = ""

    def __str__(self):
        return self.msg


class NegativeResponseError(UDSError):
    """Raised if UDS response is negative (starting with 0x7F)"""

    def __init__(self, response):
        self.msg = f"Request refused by client, got response: {response}"


class UnexpectedResponseError(UDSError):
    """Raised if UDS response is positive but should not be"""

    def __init__(self, response):
        self.msg = f"Request expected to fail but succeed, got response: {response}"


class InvalidResponseError(UDSError):
    """Raise if UDS response is not the expected one"""

    def __init__(self, command):
        self.msg = f"Invalid response for command {command}"


class ResponseNotReceivedError(UDSError):
    """Raise if no UDS response is received"""

    def __init__(self, command):
        self.msg = f"No response received for command {command}"
