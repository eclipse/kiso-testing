##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Library of SCPI commands
************************

:module: lib_scpi_commands

:synopsis: Library of helper functions used to send requests to
    instruments with SCPI protocol. This library can be used with any
    VISA instance having a write and a query method.

.. currentmodule:: lib_scpi_commands

"""
import logging
from typing import Tuple

from .lib_instruments import REGISTERED_INSTRUMENTS, SCPI_COMMANDS_DICT

log = logging.getLogger(__name__)


class LibSCPI:
    """Class containing common SCPI commands for write and query
    requests.
    """

    def __init__(self, visa_object, instrument: str = ""):
        """Constructor.

        :param visa_object: any visa object having a write and a query
            method
        :param instrument: name of the instrument in use. If registered,
             the commands adapted to this instrument's capabilities are
             used instead of the default ones.
        """
        self.visa_object = visa_object
        # Check if the instrument in use is registered
        if instrument in REGISTERED_INSTRUMENTS:
            self.instrument = instrument
            log.internal_info(
                f"{instrument} is a registered instrument: using registered commands"
            )
        else:
            self.instrument = "DEFAULT"
            log.internal_info(
                "Working with unknown instrument: using default commands."
            )

    def _send_scpi_command(
        self,
        cmd_tag: str,
        cmd_type: str,
        cmd_payload: str = "",
        cmd_validation: tuple = None,
    ) -> str:
        """Send the appropriate command to send to the instrument in
        use. Check if a command is different or not available for a
        registered instrument, uses the default command otherwise. If a
        command is registered to be unavailable for the instrument in
        use, the command is not sent, a warning is raised, and an empty
        respond message is returned.

        :param cmd_type: either 'write' or 'query'
        :param cmd_tag: command tag corresponding to the command to
            execute
        :param cmd_payload: payload of the command to execute
            (only used in write commands)
        :param cmd_validation: expected output after validation
            (only used in write commands)

        :return: the response message of the executed command
            (if query), the success code of the command (if write), or
            an empty message if the command to execute is unsupported by
            the instrument in use.
        """
        # Retrieving command to send

        command, validation = self.get_command(cmd_tag, cmd_type, cmd_validation)

        if command == "COMMAND_NOT_AVAILABLE":
            return command

        if cmd_type == "query":
            return self.visa_object.query(command)

        return self.visa_object.write(f"{command} {cmd_payload}".strip(), validation)

    def get_command(
        self, cmd_tag: str, cmd_type: str, cmd_validation: tuple = None
    ) -> Tuple:
        """Return the pre-defined command.

        :param cmd_tag: command tag corresponding to the command to
            execute
        :param cmd_type: either 'write' or 'query'
        :param cmd_validation: expected output after validation
            (only used in write commands)

        :return: the associated command plus a tuple containing the
            associated query and the expected response (if
            cmd_validation is not none) otherwise None
        """
        validation = None
        # Retrieving command to send
        if self.instrument in SCPI_COMMANDS_DICT[cmd_tag][cmd_type]:
            instr = self.instrument
        else:
            instr = "DEFAULT"
        command = SCPI_COMMANDS_DICT[cmd_tag][cmd_type][instr]

        # Check if the command is available for the instrument in use
        if command == "NOT_AVAILABLE":
            # do not send any request
            log.internal_warning(
                f"Command {cmd_type}:{cmd_tag} aborted as not available for instrument {self.instrument}"
            )
            return "COMMAND_NOT_AVAILABLE", validation

        if cmd_validation is not None:
            validation = (
                SCPI_COMMANDS_DICT[cmd_tag]["query"][instr],
                cmd_validation,
            )

        return command, validation

    def get_identification(self):
        """Get the identification information of an instrument.

        :return: the instrument's identification information
        """
        return self._send_scpi_command(
            cmd_tag="IDENTIFICATION",
            cmd_type="query",
        )

    def get_status_byte(self):
        """Get the status byte of an instrument.

        :return: the instrument's status byte
        """
        return self._send_scpi_command(
            cmd_tag="STATUS_BYTE",
            cmd_type="query",
        )

    def get_all_errors(self):
        """Get all errors of an instrument.

        return: list of off errors
        """
        return self._send_scpi_command(
            cmd_tag="ALL_ERRORS",
            cmd_type="query",
        )

    def reset(self):
        """Reset an instrument.

        :return: NO_VALIDATION status code
        """
        return self.visa_object.write("*RST")

    def self_test(self):
        """Performs a self-test of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(cmd_tag="SELF_TEST", cmd_type="query")

    def get_remote_control_state(self):
        """Get the remote control mode (ON or OFF) of an instrument.

        :return: the remote control state
        """
        return self._send_scpi_command(
            cmd_tag="REMOTE_CONTROL",
            cmd_type="query",
        )

    def set_remote_control_on(self):
        """Enables the remote control of an instrument. The
        instrument will respond to all SCPI commands.

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="REMOTE_CONTROL",
            cmd_type="write",
            cmd_payload="ON",
            cmd_validation=["REMOTE", "ON", "1"],
        )

    def set_remote_control_off(self):
        """Disable the remote control of an instrument. The
        instrument will respond to query and read commands only.

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="REMOTE_CONTROL",
            cmd_type="write",
            cmd_payload="OFF",
            cmd_validation=["LOCAL", "OFF", "0", "NONE"],
        )

    def get_output_channel(self) -> str:
        """Get the currently selected output channel of an instrument.

        :return: the currently selected output channel
        """
        return self._send_scpi_command(
            cmd_tag="OUTPUT_CHANNEL",
            cmd_type="query",
        )

    def set_output_channel(self, channel: int) -> str:
        """Set the output channel of an instrument.

        :param channel: the output channel to select on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="OUTPUT_CHANNEL",
            cmd_type="write",
            cmd_payload=channel,
            cmd_validation=f"{channel}",
        )

    def get_output_state(self) -> str:
        """Get the output status (ON or OFF, enabled or disabled) of the
        currently selected channel of an instrument.

        :return: the output state (ON or OFF)
        """
        return self._send_scpi_command(
            cmd_tag="OUTPUT_ENABLE",
            cmd_type="query",
        )

    def enable_output(self) -> str:
        """Enable output on the currently selected output channel
        of an instrument.

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="OUTPUT_ENABLE",
            cmd_type="write",
            cmd_payload="ON",
            cmd_validation=["ENABLE", "ENABLED", "ON", "1"],
        )

    def disable_output(self) -> str:
        """Disable output on the currently selected output channel
        of an instrument.

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="OUTPUT_ENABLE",
            cmd_type="write",
            cmd_payload="OFF",
            cmd_validation=["DISABLE", "DISABLED", "OFF", "0"],
        )

    def get_nominal_voltage(self) -> str:
        """Query the nominal voltage of an instrument on the selected
        channel (in V).

        :return: the nominal voltage
        """
        return self._send_scpi_command(
            cmd_tag="NOMINAL_VOLTAGE",
            cmd_type="query",
        )

    def get_nominal_current(self) -> str:
        """Query the nominal current of an instrument on the selected
        channel (in A).

        :return: the nominal current
        """
        return self._send_scpi_command(
            cmd_tag="NOMINAL_CURRENT",
            cmd_type="query",
        )

    def get_nominal_power(self) -> str:
        """Query the nominal power of an instrument on the selected
        channel (in W).

        :return: the nominal power
        """
        return self._send_scpi_command(
            cmd_tag="NOMINAL_POWER",
            cmd_type="query",
        )

    def measure_voltage(self) -> str:
        """Return the measured output voltage of an instrument (in V).

        :return: the measured voltage
        """
        return self._send_scpi_command(
            cmd_tag="MEASURE_VOLTAGE",
            cmd_type="query",
        )

    def measure_current(self) -> str:
        """Return the measured output current of an instrument (in A).

        :return: the measured current
        """
        return self._send_scpi_command(
            cmd_tag="MEASURE_CURRENT",
            cmd_type="query",
        )

    def measure_power(self) -> str:
        """Return the measured output power of an instrument (in W).

        :return: the measured power
        """
        return self._send_scpi_command(
            cmd_tag="MEASURE_POWER",
            cmd_type="query",
        )

    def get_target_voltage(self) -> str:
        """Get the desired output voltage (in V) of an instrument.

        :return: the target voltage
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE",
            cmd_type="query",
        )

    def get_target_current(self) -> str:
        """Get the desired output current (in A) of an instrument.

        :return: the target current
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT",
            cmd_type="query",
        )

    def get_target_power(self) -> str:
        """Get the desired output power (in W) of an instrument.

        :return: the target power
        """
        return self._send_scpi_command(
            cmd_tag="POWER",
            cmd_type="query",
        )

    def set_target_voltage(self, value: float) -> str:
        """Set the desired output voltage (in V) of an instrument.

        :param value: value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE",
            cmd_type="write",
            cmd_payload=value,
            cmd_validation=f"VALUE{{{value}}}",
        )

    def set_target_current(self, value: float) -> str:
        """Set the desired output current (in A) of an instrument.

        :param value: value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT",
            cmd_type="write",
            cmd_payload=value,
            cmd_validation=f"VALUE{{{value}}}",
        )

    def set_target_power(self, value: float) -> str:
        """Set the desired output power (in W) of an instrument.

        :param value: value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="POWER",
            cmd_type="write",
            cmd_payload=value,
            cmd_validation=f"VALUE{{{value}}}",
        )

    def get_voltage_limit_low(self) -> str:
        """Returns the voltage lower limit (in V) of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE_LIMIT_LOW",
            cmd_type="query",
        )

    def get_voltage_limit_high(self) -> str:
        """Returns the voltage upper limit (in V) of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE_LIMIT_HIGH",
            cmd_type="query",
        )

    def get_current_limit_low(self) -> str:
        """Returns the current lower limit (in V) of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT_LIMIT_LOW",
            cmd_type="query",
        )

    def get_current_limit_high(self) -> str:
        """Returns the current upper limit (in V) of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT_LIMIT_HIGH",
            cmd_type="query",
        )

    def get_power_limit_high(self) -> str:
        """Returns the power upper limit (in W) of an instrument.

        :return: the query's response message
        """
        return self._send_scpi_command(
            cmd_tag="POWER_LIMIT_HIGH",
            cmd_type="query",
        )

    def set_voltage_limit_low(self, limit_value: float) -> str:
        """Set the voltage lower limit (in V) of an instrument.

        :param limit_value: limit value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE_LIMIT_LOW",
            cmd_type="write",
            cmd_payload=limit_value,
            cmd_validation=f"VALUE{{{limit_value}}}",
        )

    def set_voltage_limit_high(self, limit_value: float) -> str:
        """Set the voltage upper limit (in V) of an instrument.

        :param limit_value: limit value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="VOLTAGE_LIMIT_HIGH",
            cmd_type="write",
            cmd_payload=limit_value,
            cmd_validation=f"VALUE{{{limit_value}}}",
        )

    def set_current_limit_low(self, limit_value: float) -> str:
        """Set the current lower limit (in A) of an instrument.

        :param limit_value: limit value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT_LIMIT_LOW",
            cmd_type="write",
            cmd_payload=limit_value,
            cmd_validation=f"VALUE{{{limit_value}}}",
        )

    def set_current_limit_high(self, limit_value: float) -> str:
        """Set the current upper limit (in A) of an instrument.

        :param limit_value: limit value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="CURRENT_LIMIT_HIGH",
            cmd_type="write",
            cmd_payload=limit_value,
            cmd_validation=f"VALUE{{{limit_value}}}",
        )

    def set_power_limit_high(self, limit_value: float) -> str:
        """Set the power upper limit (in W) of an instrument.

        :param limit_value: limit value to be set on the instrument

        :return: the writing operation's status code
        """
        return self._send_scpi_command(
            cmd_tag="POWER_LIMIT_HIGH",
            cmd_type="write",
            cmd_payload=limit_value,
            cmd_validation=f"VALUE{{{limit_value}}}",
        )
