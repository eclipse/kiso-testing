##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Ykush auxiliary test
********************

:module: test_ykush

:synopsis: Example test that shows how to control the Ykush usb.

.. currentmodule:: test_ykush

"""

import logging

import pykiso
from pykiso.auxiliaries import ykush_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[ykush_aux])
class ExampleYkushTest(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

    def test_run(self):
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        list_state = ykush_aux.get_all_ports_state_str()
        logging.info(f"The state of the ports are :{list_state}")

        logging.info("Power off all ports")
        ykush_aux.set_all_ports_off()

        logging.info("Check if all ports are off")
        self.assertEqual(ykush_aux.get_all_ports_state(), [0, 0, 0])

        logging.info("Power on the port 1")
        ykush_aux.set_port_on(port_number=1)

        logging.info("Get the state of the port 1")
        state_port_1 = ykush_aux.get_port_state_str(port_number=1)
        logging.info(f"Port 1 is {state_port_1}")

        logging.info("Check if the port is on")
        self.assertTrue(ykush_aux.is_port_on(port_number=1))

        logging.info("Power off the port number 1")
        ykush_aux.set_port_off(port_number=1)

        logging.info("Check if the port is off")
        self.assertTrue(ykush_aux.is_port_off(port_number=1))

        list_state = ykush_aux.get_all_ports_state_str()
        logging.info(f"The state of the ports are :{list_state}")

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
