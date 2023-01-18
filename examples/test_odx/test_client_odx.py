import logging
import time
import typing
import unittest

import pykiso
from pykiso.auxiliaries import uds_client_aux

# helper objects to build callbacks can be imported from the pykiso lib
from pykiso.lib.auxiliaries.udsaux import UdsCallback, UdsServerAuxiliary


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_client_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        pass

    def test_run(self):
        """
        sent a request to a uds server
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        response = uds_client_aux.send_uds_raw([0x10, 0x03])
        assert response == [0x50, 0x03]
        response_2 = uds_client_aux.send_uds_raw([0x22, 0xA4, 0x55])
        # negative:
        assert response_2 == [0x7F, 0x22, 0x11]
        # positive:
        # assert response_2 == [0x62, 0xA4, 0x55, 0x30, 0x2E, 0x31, 0x37, 0x2E, 0x30]

    def tearDown(self):
        pass
