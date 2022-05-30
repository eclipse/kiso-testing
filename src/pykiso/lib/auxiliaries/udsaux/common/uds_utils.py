##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
uds_utils
*********

:module: uds_utils

:synopsis: This module contains service names functions enums.

.. currentmodule:: util_utils
"""

import logging
from enum import IntEnum

log = logging.getLogger(__name__)


SERVICE_ID_TO_NAME = {
    0x10: "diagnosticSessionControl",
    0x11: "ecuReset",
    0x14: "clearDTC",
    0x19: "readDTC",
    0x22: "readDataByIdentifier",
    0x27: "securityAccess",
    0x2E: "writeDataByIdentifier",
    0x2F: "inputOutputControl",
    0x31: "routineControl",
    0x34: "requestDownload",
    0x35: "requestUpload",
    0x36: "transferData",
    0x37: "transferExit",
    0x3E: "testerPresent",
}


def get_uds_service(service_id: IntEnum) -> str or None:
    """Get uds service name function that is binded to uds instance

    :param service_id: uds service identifier

    :return: uds service function name
    """
    name = SERVICE_ID_TO_NAME.get(service_id)
    if name is None:
        log.error("UDS service ID not found")

    return name
