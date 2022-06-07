##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS server auxiliary simple example
***********************************

:module: test_uds_server

:synopsis: Example test that shows how to use the UDS server auxiliary

.. currentmodule:: test_uds_server

"""

import logging
import time
import unittest

import pykiso
from pykiso.auxiliaries import uds_aux

# helper objects to build callbacks can be imported from the pykiso lib
from pykiso.lib.auxiliaries.udsaux import (
    UdsCallback,
    UdsDownloadCallback,
    UdsServerAuxiliary,
)


def custom_callback(ecu_reset_request: list, aux: UdsServerAuxiliary) -> None:
    """Custom callback example for an ECU reset request.

    This simulates a pending response from the server before sending the
    corresponding positive response.

    :param ecu_reset_request: received ECU reset request from the client.
    :param aux: current UdsServerAuxiliary instance used in test.
    """
    for _ in range(4):
        aux.send_response([0x7F, 0x78])
        time.sleep(0.1)
    aux.send_response([0x51, 0x01])


# callbacks to register can then be built and stored in a list in order to be registered in tests
UDS_CALLBACKS = [
    # Here the response could be left out
    # It would be automatically built based on the request
    UdsCallback(request=0x3E00, response=0x7E00),
    # Use the user-defined callback function above
    UdsCallback(request=0x1101, callback=custom_callback),
    # The download functional unit is available as a pre-defined callback
    # It only requires the stmin parameter (minimum time between 2 consecutive frames, here 10ms)
    # Others (RequestUpload, RequestFileTransfer) can be implemented based on it.
    UdsDownloadCallback(stmin=10),
]


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        """Register various callbacks for the test."""
        # register all callbacks defined above
        for callback in UDS_CALLBACKS:
            uds_aux.register_callback(callback)

        # handle extended diagnostics session request
        # respond to an incoming request [0x10, 0x03] with [0x50, 0x03, 0x12, 0x34]
        uds_aux.register_callback(request=0x1003, response=0x50031234)

        # handle incoming read data by identifier request with identifier [0x01, 0x02]
        # the response will be built by:
        # - creating the positive response corresponding to the request: 0x620102
        # - appending the passed response data b'DATA': 0x620102_44415451
        # - zero-padding the response data until the expected length is reached: 0x620102_44415451_0000
        uds_aux.register_callback(
            request=0x220102, response_data=b"DATA", data_length=6
        )

    def test_run(self):
        """
        Simply wait a bit and expect the registered request to be received
        (and the corresponding response to be sent to the client).
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        time.sleep(10)
        # access the previously registered callback
        extended_diag_session_callback = uds_aux.callbacks["0x1003"]
        self.assertGreater(
            extended_diag_session_callback.call_count,
            0,
            "Expected UDS request was not sent by the client after 10s",
        )

    def tearDown(self):
        """Unregister all previously registered callbacks."""
        for callback in uds_aux.callbacks:
            uds_aux.unregister_callback(callback)
