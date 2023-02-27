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

:module: test_client_odx

:synopsis: Example test to use with odx configured uds server
    Showcases negative and positive responses

.. currentmodule:: test_client_odx
"""
import logging

import pykiso
from pykiso.auxiliaries import uds_client_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_client_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        pass

    def test_run(self):
        """
        Send two uds requests, expecting one negative and one positive response
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # test a expected negative response:
        negative_response = uds_client_aux.send_uds_raw([0x22, 0xA4, 0x55])
        assert negative_response == [0x7F, 0x22, 0x11]
        # test a expected positive response:
        positive_response = uds_client_aux.send_uds_raw([0x22, 0xA4, 0x56])
        assert positive_response == [0x62, 0xA4, 0x56, 0x31, 0x32, 0x33]

    def tearDown(self):
        pass
