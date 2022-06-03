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


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
class ExampleUdsServerTest(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        uds_aux.register_callback(0x1003, 0x50031234)

    def test_run(self):
        """
        Simply wait a bit and expect the registered request to be received
        (and the corresponding response to be sent to the client).
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        time.sleep(10)
        extended_diag_session_callback = uds_aux.callbacks["0x1003"]
        self.assertGreater(
            extended_diag_session_callback.call_count,
            0,
            "Expected UDS request was not sent by the client after 10s",
        )

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        pass
