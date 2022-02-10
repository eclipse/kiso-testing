##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Instrument control auxiliary plugin
***********************************

:module: instrument_control_auxiliary

:synopsis: implementation of existing InstrumentControlAuxiliary for
    Robot framework usage.

.. currentmodule:: instrument_control_auxiliary

"""

from robot.api.deco import keyword, library

from ..auxiliaries.instrument_control_auxiliary import (
    InstrumentControlAuxiliary as InstAux,
)
from .aux_interface import RobotAuxInterface


@library(version="0.1.0")
class InstrumentControlAuxiliary(RobotAuxInterface):
    """Robot framework plugin for InstrumentControlAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=InstAux)

    @keyword(name="Write")
    def write(
        self, write_command: str, aux_alias: str, validation: tuple = None
    ) -> str:
        """Send a write request to the instrument and then returns if
        the value was successfully written. A query is sent immediately
        after the writing and the answer is compared to the expected
        one.

        :param write_command: write command to send
        :param aux_alias: auxiliary's alias
        :param validation: tuple of the form
            (validation command (str), expected output (str))

        :return: status message depending on the command validation:
            SUCCESS, FAILURE or NO_VALIDATION
        """
        aux = self._get_aux(aux_alias)
        return aux.write(write_command, validation)

    @keyword(name="Read")
    def read(self, aux_alias: str) -> str:
        """Send a read request to the instrument.

        :param aux_alias: auxiliary's alias

        :return: Response message, None if the request expired with a
            timeout.
        """
        aux = self._get_aux(aux_alias)
        return aux.read()

    @keyword(name="Query")
    def query(self, query_command: str, aux_alias: str) -> str:
        """Send a query request to the instrument.

        :param query_command: query command to send
        :param aux_alias: auxiliary's alias

        :return: Response message, None if the request expired with a
            timeout.
        """
        aux = self._get_aux(aux_alias)
        return aux.query(query_command)

    @keyword(name="Get identification")
    def get_identification(self, aux_alias: str) -> str:
        """Get the identification information of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the instrument's identification information
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_identification()

    @keyword(name="Get status byte")
    def get_status_byte(self, aux_alias: str) -> str:
        """Get the status byte of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the intrument's status byte
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_status_byte()

    @keyword(name="Get all errors")
    def get_all_errors(self, aux_alias: str) -> str:
        """Get all errors of an instrument.

        :param aux_alias: auxiliary's alias

        return: list of off errors
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_all_errors()

    @keyword(name="Reset")
    def reset(self, aux_alias: str) -> str:
        """Reset an instrument.

        :param aux_alias: auxiliary's alias

        :return: NO_VALIDATION status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.reset()

    @keyword(name="Self test")
    def self_test(self, aux_alias: str) -> str:
        """Performs a self-test of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.self_test()

    @keyword(name="Get remote control state")
    def get_remote_control_state(self, aux_alias: str) -> str:
        """Get the remote control mode (ON or OFF) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the remote control state
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_remote_control_state()

    @keyword(name="Set remote control on")
    def set_remote_control_on(self, aux_alias: str) -> str:
        """Enables the remote control of an instrument. The instrument
        will respond to all SCPI commands.

        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_remote_control_on()

    @keyword(name="Set remote control off")
    def set_remote_control_off(self, aux_alias: str) -> str:
        """Disable the remote control of an instrument. The instrument
        will respond to query and read commands only.

        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_remote_control_off()

    @keyword(name="Get output channel")
    def get_output_channel(self, aux_alias: str) -> str:
        """Get the currently selected output channel of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the currently selected output channel
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_output_channel()

    @keyword(name="Set output channel")
    def set_output_channel(self, channel: int, aux_alias: str) -> str:
        """Set the output channel of an instrument.

        :param channel: the output channel to select on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_output_channel(channel)

    @keyword(name="Get output state")
    def get_output_state(self, aux_alias: str) -> str:
        """Get the output status (ON or OFF, enabled or disabled) of the
        currently selected channel of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the output state (ON or OFF)
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_output_state()

    @keyword(name="Enable output")
    def enable_output(self, aux_alias: str) -> str:
        """Enable output on the currently selected output channel of an
        instrument.

        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.enable_output()

    @keyword(name="Disable output")
    def disable_output(self, aux_alias: str) -> str:
        """Disable output on the currently selected output channel of an
        instrument.

        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.disable_output()

    @keyword(name="Get nominal voltage")
    def get_nominal_voltage(self, aux_alias: str) -> str:
        """Query the nominal voltage of an instrument on the selected
        channel (in V).

        :param aux_alias: auxiliary's alias

        :return: the nominal voltage
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_nominal_voltage()

    @keyword(name="Get nominal current")
    def get_nominal_current(self, aux_alias: str) -> str:
        """Query the nominal current of an instrument on the selected
        channel (in A)

        :param aux_alias: auxiliary's alias

        :return: the nominal current
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_nominal_current()

    @keyword(name="Get nominal power")
    def get_nominal_power(self, aux_alias: str) -> str:
        """Query the nominal power of an instrument on the selected
        channel (in W).

        :param aux_alias: auxiliary's alias

        :return: the nominal power
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_nominal_power()

    @keyword(name="Measure voltage")
    def measure_voltage(self, aux_alias: str) -> str:
        """Return the measured output voltage of an instrument (in V).

        :param aux_alias: auxiliary's alias

        :return: the measured voltage
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.measure_voltage()

    @keyword(name="Measure current")
    def measure_current(self, aux_alias: str) -> str:
        """Return the measured output current of an instrument (in A).

        :param aux_alias: auxiliary's alias

        :return: the measured current
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.measure_current()

    @keyword(name="Measure power")
    def measure_power(self, aux_alias: str) -> str:
        """Return the measured output power of an instrument (in W).

        :param aux_alias: auxiliary's alias

        :return: the measured power
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.measure_power()

    @keyword(name="Get target voltage")
    def get_target_voltage(self, aux_alias: str) -> str:
        """Get the desired output voltage (in V) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the target voltage
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_target_voltage()

    @keyword(name="Get target current")
    def get_target_current(self, aux_alias: str) -> str:
        """Get the desired output current (in A) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the target current
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_target_current()

    @keyword(name="Get target power")
    def get_target_power(self, aux_alias: str) -> str:
        """Get the desired output power (in W) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the target power
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_target_power()

    @keyword(name="Set target voltage")
    def set_target_voltage(self, value: float, aux_alias: str) -> str:
        """Set the desired output voltage (in V) of an instrument.

        :param value: value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_target_voltage(value)

    @keyword(name="Set target current")
    def set_target_current(self, value: float, aux_alias: str) -> str:
        """Set the desired output current (in A) of an instrument.

        :param value: value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_target_current(value)

    @keyword(name="Set target power")
    def set_target_power(self, value: float, aux_alias: str) -> str:
        """Set the desired output power (in W) of an instrument.

        :param value: value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_target_power(value)

    @keyword(name="Get voltage limit low")
    def get_voltage_limit_low(self, aux_alias: str) -> str:
        """Returns the voltage lower limit (in V) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_voltage_limit_low()

    @keyword(name="Get voltage limit high")
    def get_voltage_limit_high(self, aux_alias: str) -> str:
        """Returns the voltage upper limit (in V) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_voltage_limit_high()

    @keyword(name="Get current limit low")
    def get_current_limit_low(self, aux_alias: str) -> str:
        """Returns the current lower limit (in V) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_current_limit_low()

    @keyword(name="Get current limit high")
    def get_current_limit_high(self, aux_alias: str) -> str:
        """Returns the current upper limit (in V) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_current_limit_high()

    @keyword(name="Get power limit high")
    def get_power_limit_high(self, aux_alias: str) -> str:
        """Returns the power upper limit (in W) of an instrument.

        :param aux_alias: auxiliary's alias

        :return: the query's response message
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.get_power_limit_high()

    @keyword(name="Set voltage limit low")
    def set_voltage_limit_low(self, limit_value: float, aux_alias: str) -> str:
        """Set the voltage lower limit (in V) of an instrument.

        :param limit_value: limit value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_voltage_limit_low(limit_value)

    @keyword(name="Set voltage limit high")
    def set_voltage_limit_high(self, limit_value: float, aux_alias: str) -> str:
        """Set the voltage upper limit (in V) of an instrument.

        :param limit_value: limit value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_voltage_limit_high(limit_value)

    @keyword(name="Set current limit low")
    def set_current_limit_low(self, limit_value: float, aux_alias: str) -> str:
        """Set the current lower limit (in A) of an instrument.

        :param limit_value: limit value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_current_limit_low(limit_value)

    @keyword(name="Set current limit high")
    def set_current_limit_high(self, limit_value: float, aux_alias: str) -> str:
        """Set the current upper limit (in A) of an instrument.

        :param limit_value: limit value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_current_limit_high(limit_value)

    @keyword(name="Set power limit high")
    def set_power_limit_high(self, limit_value: float, aux_alias: str) -> str:
        """Set the power upper limit (in W) of an instrument.

        :param limit_value: limit value to be set on the instrument
        :param aux_alias: auxiliary's alias

        :return: the writing operation's status code
        """
        aux = self._get_aux(aux_alias)
        return aux.helpers.set_power_limit_high(limit_value)
