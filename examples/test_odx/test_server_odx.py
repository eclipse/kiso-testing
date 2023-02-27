##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS server auxiliary simple example
***********************************

:module: test_server_odx

:synopsis: Example test that shows how to use the UDS server auxiliary with dict
    based callbacks. Showcases a negative and a positive response configuration

.. currentmodule:: test_server_odx
"""

import logging
import time
from copy import copy

from uds import IsoServices

import pykiso
from pykiso.auxiliaries import uds_server_aux

# helper objects to build callbacks can be imported from the pykiso lib
from pykiso.lib.auxiliaries.udsaux import UdsCallback
from pykiso.lib.auxiliaries.udsaux.common.uds_response import (
    NegativeResponseCode,
)

UDS_CALLBACKS = [
    UdsCallback(
        request={
            "service": IsoServices.ReadDataByIdentifier,
            "data": {"parameter": "SoftwareVersion"},
        },
        response={"NEGATIVE": NegativeResponseCode.SERVICE_NOT_SUPPORTED},
    ),
    UdsCallback(
        request={
            "service": IsoServices.ReadDataByIdentifier,
            "data": {"parameter": "HardwareVersion"},
        },
        response={"HardwareVersion": "123"},
    ),
]


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_server_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        """Register various callbacks for the test."""
        # register all callbacks defined above
        for callback in UDS_CALLBACKS:
            uds_server_aux.register_callback(callback)

    def test_run(self):
        """
        Simply wait a bit and expect the registered requests to be received
        (and the corresponding response to be sent to the client).
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        time.sleep(5)
        # access the previously registered callback
        read_software_version = uds_server_aux.callbacks[
            "ReadDataByIdentifier.SoftwareVersion"
        ]
        self.assertGreater(
            read_software_version.call_count,
            0,
            "Expected ODX UDS request was not sent by the client after 10s",
        )

        read_hardware_version = uds_server_aux.callbacks["0x22A456"]
        self.assertGreater(
            read_hardware_version.call_count,
            0,
            "Expected ODX UDS request was not sent by the client after 10s",
        )

    def tearDown(self):
        """Unregister all previously registered callbacks."""
        for callback in uds_server_aux.callbacks.copy():
            uds_server_aux.unregister_callback(callback)
