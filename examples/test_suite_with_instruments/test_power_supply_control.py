##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Intrument control auxiliary test
********************************

:module: test_power_supply_control

:synopsis: Example test that shows how to manipulate an instrument.
    This test will send several query and write commands thanks to the
    SCPI protocol.This example test was tested with a EA PSI 9000 T
    power supply.

.. currentmodule:: test_power_supply_control

.. warning:: Each instrument has different functionalities. Thus, the
    instrument might or might not respond to a certain SCPI command
    (you will get a timeout error in the latter case). Please see the
    datasheet of the instrument that you are using for more info.

"""

import logging
import time

import pykiso
from pykiso.auxiliaries import instr_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[instr_aux])
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

        logging.info("---General information about the instrument:")
        # using the auxiliary's 'query' method
        logging.info(f"Info: {instr_aux.query('*IDN?')}")
        # using the commands from the library
        logging.info(f"Status byte: {instr_aux.helpers.get_status_byte()}")
        logging.info(f"Errors: {instr_aux.helpers.get_all_errors()}")
        logging.info(f"Perform a self-test: {instr_aux.helpers.self_test()}")

        # Remote Control
        logging.info("Remote control")
        instr_aux.helpers.set_remote_control_off()
        instr_aux.helpers.set_remote_control_on()

        # Nominal values
        logging.info("---Nominal values:")
        logging.info(f"Nominal voltage: {instr_aux.helpers.get_nominal_voltage()}")
        logging.info(f"Nominal current: {instr_aux.helpers.get_nominal_current()}")
        logging.info(f"Nominal power: {instr_aux.helpers.get_nominal_power()}")

        # Current values
        logging.info("---Measuring current values:")
        logging.info(f"Measured voltage: {instr_aux.helpers.measure_voltage()}")
        logging.info(f"Measured current: {instr_aux.helpers.measure_current()}")
        logging.info(f"Measured power: {instr_aux.helpers.measure_power()}")

        # Limit values
        logging.info("---Limit values:")
        logging.info(f"Voltage limit low: {instr_aux.helpers.get_voltage_limit_low()}")
        logging.info(
            f"Voltage limit high: {instr_aux.helpers.get_voltage_limit_high()}"
        )
        logging.info(f"Current limit low: {instr_aux.helpers.get_current_limit_low()}")
        logging.info(
            f"Current limit high: {instr_aux.helpers.get_current_limit_high()}"
        )
        logging.info(f"Power limit high: {instr_aux.helpers.get_power_limit_high()}")

        # Test scenario
        logging.info("Scenario: apply 36V on the selected channel for 1s")
        dc_voltage = 36.0  # V
        dc_current = 1.0  # A
        logging.info(
            f"Set voltage to {dc_voltage}V: {instr_aux.helpers.set_target_voltage(dc_voltage)}"
        )
        logging.info(
            f"Set current to {dc_current}A: {instr_aux.helpers.set_target_current(dc_current)}"
        )
        logging.info(f"Switch on output: {instr_aux.helpers.enable_output()}")
        logging.info("sleeping for 0.5s")
        time.sleep(0.5)
        logging.info(f"measured voltage: {instr_aux.helpers.measure_voltage()}")
        logging.info(f"measured current: {instr_aux.helpers.measure_current()}")
        time.sleep(0.5)
        logging.info(f"Switch off output: {instr_aux.helpers.disable_output()}")

        # Example of a command that would result in FAILURE: instr_aux.helpers.set_target_voltage(1000)
        # Be careful, this command could select the highest voltage target possible on some instrument,
        # or have no effect on others...

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
