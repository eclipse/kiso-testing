import logging
import time
import typing
import unittest
from copy import copy

from uds import IsoServices

import pykiso
from pykiso.auxiliaries import uds_server_aux

# helper objects to build callbacks can be imported from the pykiso lib
from pykiso.lib.auxiliaries.udsaux import UdsCallback, UdsServerAuxiliary
from pykiso.lib.auxiliaries.udsaux.common.uds_response import (
    NegativeResponseCode,
)

UDS_CALLBACKS = [
    UdsCallback(request=0x1003, response=0x5003),
    # UdsCallback(
    #     request={
    #         "service": IsoServices.ReadDataByIdentifier,
    #         "data": {"parameter": "SoftwareVersion"},
    #     },
    #     # also works without response
    #     response={"SoftwareVersion": "0.17.0"},
    # ),
    UdsCallback(
        request={
            "service": IsoServices.ReadDataByIdentifier,
            "data": {"parameter": "SoftwareVersion"},
        },
        response={"NEGATIVE": NegativeResponseCode.SERVICE_NOT_SUPPORTED},
    ),
]


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_server_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        """Register various callbacks for the test."""
        # register all callbacks defined above
        for callback in UDS_CALLBACKS:
            uds_server_aux.register_callback(callback)
        logging.info("-----> Waiting for requests")

    def test_run(self):
        """
        Simply wait a bit and expect the registered request to be received
        (and the corresponding response to be sent to the client).
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        time.sleep(5)
        # access the previously registered callback
        extended_diag_session_callback = uds_server_aux.callbacks["0x1003"]
        self.assertGreater(
            extended_diag_session_callback.call_count,
            0,
            "Expected UDS request was not sent by the client after 10s",
        )
        read_by_id_callback = uds_server_aux.callbacks["0x22A455"]
        self.assertGreater(
            read_by_id_callback.call_count,
            0,
            "Expected ODX UDS request was not sent by the client after 10s",
        )

    def tearDown(self):
        """Unregister all previously registered callbacks."""
        for callback in uds_server_aux.callbacks.copy():
            uds_server_aux.unregister_callback(callback)
