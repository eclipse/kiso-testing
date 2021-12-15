##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

""" Test module for instrument_control_auxiliary.lib_scpi_commands.py"""

import pytest

from pykiso.lib.auxiliaries.instrument_control_auxiliary import (
    lib_scpi_commands,
)
from pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_instruments import (
    SCPI_COMMANDS_DICT,
)


class MockVisaObject:
    def __init__(self, instrument: str = "", value: float = 42.00):
        self.instrument = instrument
        self.value = value

    def write(self, write_command: str, validation: tuple = None):
        if validation is not None:
            return f"response write {write_command} with successful validation"
        else:
            return f"response write {write_command}"

    def query(self, query_command: str):
        if query_command == "QUERY_VALUE":
            return "42.00 V"
        else:
            return f"response query {query_command}"


MOCK_REGISTERED_INSTRUMENTS = ["Special-instrument", "Special-instrument-2"]
MOCK_SCPI_COMMANDS_DICT = {
    "TAG": {
        "query": {
            "DEFAULT": "DEFAULT_CMD?",
            "Special-instrument": "SPECIAL_CMD?",
            "Special-instrument-2": "NOT_AVAILABLE",
        },
        "write": {
            "DEFAULT": "DEFAULT_CMD",
            "Special-instrument": "SPECIAL_CMD",
            "Special-instrument-2": "NOT_AVAILABLE",
        },
    },
}


def test_lib_SCPI_command_init():
    """Test init"""

    visa_object = MockVisaObject()

    lib = lib_scpi_commands.LibSCPI(visa_object)

    assert lib.visa_object == visa_object


def test_lib_SCPI_command_init_registered_instrument():
    """Test init"""

    visa_object = MockVisaObject()

    for inst in lib_scpi_commands.REGISTERED_INSTRUMENTS:
        lib = lib_scpi_commands.LibSCPI(visa_object)
        assert lib.visa_object == visa_object


@pytest.mark.parametrize(
    "MOCK_REGISTERED_INSTRUMENTS, MOCK_SCPI_COMMANDS_DICT, value",
    [
        (MOCK_REGISTERED_INSTRUMENTS, MOCK_SCPI_COMMANDS_DICT, 10.0),
    ],
)
def test__send_scpi_command(
    mocker, MOCK_REGISTERED_INSTRUMENTS, MOCK_SCPI_COMMANDS_DICT, value
):
    """Test _send_scpi_command"""

    mocker.patch.object(
        lib_scpi_commands, "REGISTERED_INSTRUMENTS", new=MOCK_REGISTERED_INSTRUMENTS
    )
    mocker.patch.object(
        lib_scpi_commands, "SCPI_COMMANDS_DICT", new=MOCK_SCPI_COMMANDS_DICT
    )

    # Test with no provided instrument
    visa_object = MockVisaObject()
    lib = lib_scpi_commands.LibSCPI(visa_object)
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="query")
        == "response query DEFAULT_CMD?"
    )
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="write")
        == "response write DEFAULT_CMD"
    )

    # Test write command with validation
    assert (
        lib._send_scpi_command(
            cmd_tag="TAG",
            cmd_type="write",
            cmd_payload=value,
            cmd_validation="VALUE_SET",
        )
        == f"response write DEFAULT_CMD {value} with successful validation"
    )

    # Test detection of registered instruments
    lib = lib_scpi_commands.LibSCPI(visa_object, "Special-instrument")
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="query")
        == "response query SPECIAL_CMD?"
    )
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="write")
        == "response write SPECIAL_CMD"
    )

    # Test command not available
    lib = lib_scpi_commands.LibSCPI(visa_object, "Special-instrument-2")
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="query")
        == "COMMAND_NOT_AVAILABLE"
    )
    assert (
        lib._send_scpi_command(cmd_tag="TAG", cmd_type="write")
        == "COMMAND_NOT_AVAILABLE"
    )


@pytest.mark.parametrize(
    "value",
    [(10.0)],
)
def test_library_functions(value):
    """Test library functions with default instrument"""

    visa_object = MockVisaObject()
    lib = lib_scpi_commands.LibSCPI(visa_object)

    # General
    assert (
        lib.get_identification()
        == f"response query {SCPI_COMMANDS_DICT['IDENTIFICATION']['query']['DEFAULT']}"
    )
    assert (
        lib.get_status_byte()
        == f"response query {SCPI_COMMANDS_DICT['STATUS_BYTE']['query']['DEFAULT']}"
    )
    assert lib.reset() == f"response write *RST"
    assert (
        lib.self_test()
        == f"response query {SCPI_COMMANDS_DICT['SELF_TEST']['query']['DEFAULT']}"
    )
    assert (
        lib.get_all_errors()
        == f"response query {SCPI_COMMANDS_DICT['ALL_ERRORS']['query']['DEFAULT']}"
    )

    # Remote control
    assert (
        lib.get_remote_control_state()
        == f"response query {SCPI_COMMANDS_DICT['REMOTE_CONTROL']['query']['DEFAULT']}"
    )
    assert (
        lib.set_remote_control_on()
        == f"response write {SCPI_COMMANDS_DICT['REMOTE_CONTROL']['write']['DEFAULT']} ON with successful validation"
    )
    assert (
        lib.set_remote_control_off()
        == f"response write {SCPI_COMMANDS_DICT['REMOTE_CONTROL']['write']['DEFAULT']} OFF with successful validation"
    )

    # Nominal values
    assert (
        lib.get_nominal_voltage()
        == f"response query {SCPI_COMMANDS_DICT['NOMINAL_VOLTAGE']['query']['DEFAULT']}"
    )
    assert (
        lib.get_nominal_current()
        == f"response query {SCPI_COMMANDS_DICT['NOMINAL_CURRENT']['query']['DEFAULT']}"
    )
    assert (
        lib.get_nominal_power()
        == f"response query {SCPI_COMMANDS_DICT['NOMINAL_POWER']['query']['DEFAULT']}"
    )

    # Measurement
    assert (
        lib.measure_voltage()
        == f"response query {SCPI_COMMANDS_DICT['MEASURE_VOLTAGE']['query']['DEFAULT']}"
    )
    assert (
        lib.measure_current()
        == f"response query {SCPI_COMMANDS_DICT['MEASURE_CURRENT']['query']['DEFAULT']}"
    )
    assert (
        lib.measure_power()
        == f"response query {SCPI_COMMANDS_DICT['MEASURE_POWER']['query']['DEFAULT']}"
    )

    # Channel selection and enable
    assert (
        lib.get_output_channel()
        == f"response query {SCPI_COMMANDS_DICT['OUTPUT_CHANNEL']['query']['DEFAULT']}"
    )
    assert (
        lib.set_output_channel(int(value))
        == f"response write {SCPI_COMMANDS_DICT['OUTPUT_CHANNEL']['write']['DEFAULT']} {int(value)} with successful validation"
    )
    assert (
        lib.get_output_state()
        == f"response query {SCPI_COMMANDS_DICT['OUTPUT_ENABLE']['query']['DEFAULT']}"
    )
    assert (
        lib.enable_output()
        == f"response write {SCPI_COMMANDS_DICT['OUTPUT_ENABLE']['write']['DEFAULT']} ON with successful validation"
    )
    assert (
        lib.disable_output()
        == f"response write {SCPI_COMMANDS_DICT['OUTPUT_ENABLE']['write']['DEFAULT']} OFF with successful validation"
    )

    # Target values
    assert (
        lib.get_target_voltage()
        == f"response query {SCPI_COMMANDS_DICT['VOLTAGE']['query']['DEFAULT']}"
    )
    assert (
        lib.get_target_current()
        == f"response query {SCPI_COMMANDS_DICT['CURRENT']['query']['DEFAULT']}"
    )
    assert (
        lib.get_target_power()
        == f"response query {SCPI_COMMANDS_DICT['POWER']['query']['DEFAULT']}"
    )
    assert (
        lib.set_target_voltage(value)
        == f"response write {SCPI_COMMANDS_DICT['VOLTAGE']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_target_current(value)
        == f"response write {SCPI_COMMANDS_DICT['CURRENT']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_target_power(value)
        == f"response write {SCPI_COMMANDS_DICT['POWER']['write']['DEFAULT']} {value} with successful validation"
    )

    # Limits values
    assert (
        lib.get_voltage_limit_low()
        == f"response query {SCPI_COMMANDS_DICT['VOLTAGE_LIMIT_LOW']['query']['DEFAULT']}"
    )
    assert (
        lib.get_voltage_limit_high()
        == f"response query {SCPI_COMMANDS_DICT['VOLTAGE_LIMIT_HIGH']['query']['DEFAULT']}"
    )
    assert (
        lib.get_current_limit_low()
        == f"response query {SCPI_COMMANDS_DICT['CURRENT_LIMIT_LOW']['query']['DEFAULT']}"
    )
    assert (
        lib.get_current_limit_high()
        == f"response query {SCPI_COMMANDS_DICT['CURRENT_LIMIT_HIGH']['query']['DEFAULT']}"
    )
    assert (
        lib.get_power_limit_high()
        == f"response query {SCPI_COMMANDS_DICT['POWER_LIMIT_HIGH']['query']['DEFAULT']}"
    )
    assert (
        lib.set_voltage_limit_low(value)
        == f"response write {SCPI_COMMANDS_DICT['VOLTAGE_LIMIT_LOW']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_voltage_limit_high(value)
        == f"response write {SCPI_COMMANDS_DICT['VOLTAGE_LIMIT_HIGH']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_current_limit_low(value)
        == f"response write {SCPI_COMMANDS_DICT['CURRENT_LIMIT_LOW']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_current_limit_high(value)
        == f"response write {SCPI_COMMANDS_DICT['CURRENT_LIMIT_HIGH']['write']['DEFAULT']} {value} with successful validation"
    )
    assert (
        lib.set_power_limit_high(value)
        == f"response write {SCPI_COMMANDS_DICT['POWER_LIMIT_HIGH']['write']['DEFAULT']} {value} with successful validation"
    )
