##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS auxiliary simple example
****************************

:module: test_raw_uds

:synopsis: Example test that shows how to use the uds auxiliary

.. currentmodule:: test_raw_uds

"""

import logging
import time
import unittest

import pykiso
from pykiso.auxiliaries import uds_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
class ExampleUdsTest(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        pass

    def test_run(self):
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        """
        Simply go in extended session.

        The equivalent command using an ODX file would be :

        extendedSession_req = {
            "service": IsoServices.DiagnosticSessionControl,
            "data": {"parameter": "Extended Diagnostic Session"},
        }
        diag_session_response = uds_aux.send_uds_config(extendedSession_req)
        """
        diag_session_response = uds_aux.send_uds_raw([0x10, 0x03])
        self.assertEqual(diag_session_response[:2], [0x50, 0x03])

        """
        If no communication is exchanged with the client for more than 5 seconds
        the control unit automatically exits the current session and returns to the
        "Default Session" back, and might go to sleep mode.

        To avoid this issue, if test steps take too long between uds commands the
        context manager tester present sender can be used. It will send at a defined period
        a Tester Present, to signal to the device that the client is still present.
        """
        # Sends Tester Present every 5 seconds
        with uds_aux.tester_present_sender(period=5):
            time.sleep(6)
            # Go into safety system session
            uds_aux.send_uds_raw([0x10, 0x04])

        # It is also possible to do it with start and stop methods
        uds_aux.start_tester_present_sender(period=5)
        time.sleep(6)
        response = uds_aux.send_uds_raw([0x10, 0x04])
        # It is possible to check the maximum interval between to pending response messages
        assert uds_aux.check_max_pending_time(response, 3)
        uds_aux.stop_tester_present_sender()

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        pass
