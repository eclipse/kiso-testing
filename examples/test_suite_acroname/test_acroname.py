##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Acroname auxiliary test
***********************

:module: test_acroname

:synopsis: Example test that shows how to control the acroname usb.

.. currentmodule:: test_acroname

"""

import logging
import time

import pykiso
from pykiso.auxiliaries import acro_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[acro_aux])
class TestWithPowerSupply(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

    def test_run(self):
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        logging.info("Power off all usb port")

        for port_number in range(4):
            acro_aux.set_port_disable(port_number)

        time.sleep(2)

        logging.info("Power on all usb ports")

        for port_number in range(4):
            acro_aux.set_port_enable(port_number)

        time.sleep(2)

        logging.info("Set current limit on all usb ports to 1000 mA")

        for port_number in range(4):
            acro_aux.set_port_current_limit(port_number, 1000, "mA")

        logging.info("Take measurements on all usb ports")
        for port_number in range(4):
            voltage = acro_aux.get_port_voltage(port_number, "V")
            current = acro_aux.get_port_current(port_number, "mA")
            current_limit = acro_aux.get_port_current_limit(port_number, "mA")
            logging.info(
                f"Measured {voltage:.3f}V {current:.3f}mA "
                f"currentlimit {current_limit:.3f}mA on usb Port {port_number}"
            )

        logging.info("Set current limit on all usb ports to maximum -> 2500 mA")
        for port_number in range(4):
            current_limit = acro_aux.set_port_current_limit(port_number, 2500, "mA")

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
