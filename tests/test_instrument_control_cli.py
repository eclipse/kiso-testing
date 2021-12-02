##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pytest

import pykiso
from pykiso.lib.auxiliaries.instrument_control_auxiliary import (
    instrument_control_cli,
)


class MockVisaObject:
    """Mocker of Visa object (connector or auxiliary)"""

    def __init__(self, **kwargs):
        self.resource_name = "messagebased_resource"

    def open(self):
        pass

    def close(self):
        pass

    def write(self, write_command):
        return f"write {write_command}"

    def query(self, query_commnad):
        return f"query {query_commnad}"


MOCK_REGISTERED_INSTRUMENTS = ["Special-instrument"]


class MockLibSCPI:
    def __init__(self, visa_object, instrument: str = ""):
        self.visa_object = MockVisaObject()
        if instrument in MOCK_REGISTERED_INSTRUMENTS:
            self.instrument = instrument
        else:
            self.instrument = "DEFAULT"

    def _send_scpi_command(
        self,
        cmd_tag: str,
        cmd_type: str,
        cmd_payload: str = "",
        cmd_validation: tuple = None,
    ) -> str:
        return "resp"

    def get_identification(self):
        return "resp"

    def get_status_byte(self):
        return "resp"

    def get_all_errors(self):
        return "resp"

    def reset(self):
        return "resp"

    def self_test(self):
        return "resp"

    def get_remote_control_state(self):
        return "resp"

    def set_remote_control_on(self):
        return "resp"

    def set_remote_control_off(self):
        return "resp"

    def get_output_channel(self) -> str:
        return "resp"

    def set_output_channel(self, channel: int) -> str:
        return "resp"

    def get_output_state(self) -> str:
        return "resp"

    def enable_output(self) -> str:
        return "resp"

    def disable_output(self) -> str:
        return "resp"

    def get_nominal_voltage(self) -> str:
        return "resp"

    def get_nominal_current(self) -> str:
        return "resp"

    def get_nominal_power(self) -> str:
        return "resp"

    def measure_voltage(self) -> str:
        return "resp"

    def measure_current(self) -> str:
        return "resp"

    def measure_power(self) -> str:
        return "resp"

    def get_target_voltage(self) -> str:
        return "resp"

    def get_target_current(self) -> str:
        return "resp"

    def get_target_power(self) -> str:
        return "resp"

    def set_target_voltage(self, value: float) -> str:
        return "resp"

    def set_target_current(self, value: float) -> str:
        return "resp"

    def set_target_power(self, value: float) -> str:
        return "resp"

    def get_voltage_limit_low(self) -> str:
        return "resp"

    def get_voltage_limit_high(self) -> str:
        return "resp"

    def get_current_limit_low(self) -> str:
        return "resp"

    def get_current_limit_high(self) -> str:
        return "resp"

    def get_power_limit_high(self) -> str:
        return "resp"

    def set_voltage_limit_low(self, limit_value: float) -> str:
        return "resp"

    def set_voltage_limit_high(self, limit_value: float) -> str:
        return "resp"

    def set_current_limit_low(self, limit_value: float) -> str:
        return "resp"

    def set_current_limit_high(self, limit_value: float) -> str:
        return "resp"

    def set_power_limit_high(self, limit_value: float) -> str:
        return "resp"


class MockInstrumentControlAuxiliary:
    def __init__(
        self, com=MockVisaObject(), instrument="", output_channel=None, **kwargs
    ):
        self.channel = com
        self.instrument = instrument
        self.output_channel = output_channel
        self.helpers = MockLibSCPI(self, self.instrument)

    def create_instance(self):
        pass

    def delete_instance(self):
        pass

    def close(self):
        pass

    def write(self, write_command):
        return f"write {write_command}"

    def read(self):
        return "read"

    def query(self, query_commnad):
        return f"query {query_commnad}"


@pytest.mark.parametrize(
    "level, expected_level",
    [
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
    ],
)
def test_initialize_logging(level, expected_level):
    """Test the logging initialization"""
    logger = instrument_control_cli.initialize_logging(level)

    assert logger.isEnabledFor(expected_level)


@pytest.mark.parametrize(
    "port, ip_address, baud_rate",
    [
        (4, "10.10.10.10", 115200),
    ],
)
def test_setup_interface(mocker, port, ip_address, baud_rate):
    """Test setup_interface"""
    mocker.patch.object(instrument_control_cli, "VISASerial", new=MockVisaObject)
    mocker.patch.object(instrument_control_cli, "VISATcpip", new=MockVisaObject)
    mocker.patch.object(instrument_control_cli, "CCTcpip", new=MockVisaObject)
    mocker.patch.object(
        instrument_control_cli,
        "InstrumentControlAuxiliary",
        new=MockInstrumentControlAuxiliary,
    )

    # Test successful
    serial_inst = instrument_control_cli.setup_interface(
        interface="VISA_SERIAL", port=port, baud_rate=baud_rate
    )
    tcpip_inst = instrument_control_cli.setup_interface(
        interface="VISA_TCPIP",
        ip_address=ip_address,
        name=MOCK_REGISTERED_INSTRUMENTS[0],
    )
    socket_inst = instrument_control_cli.setup_interface(
        interface="SOCKET_TCPIP",
        ip_address=ip_address,
        port=port,
    )
    assert isinstance(serial_inst, instrument_control_cli.InstrumentControlAuxiliary)
    assert isinstance(tcpip_inst, instrument_control_cli.InstrumentControlAuxiliary)
    assert isinstance(socket_inst, instrument_control_cli.InstrumentControlAuxiliary)

    # Test failures
    with pytest.raises(TypeError):
        # no interface provided
        instrument_control_cli.setup_interface()
    with pytest.raises(ConnectionAbortedError):
        # no interface provided
        instrument_control_cli.setup_interface(interface="Unknown")
    with pytest.raises(ConnectionAbortedError):
        # no serial port provided with SERIAL interface
        instrument_control_cli.setup_interface(interface="VISA_SERIAL")
    with pytest.raises(ConnectionAbortedError):
        # no ip address provided with VISA_TCPIP interface
        instrument_control_cli.setup_interface(interface="VISA_TCPIP")
    with pytest.raises(ConnectionAbortedError):
        # no ip address nor port provided with SOCKET_TCPIP interface
        instrument_control_cli.setup_interface(interface="SOCKET_TCPIP")


def test_perform_actions_flags(mocker):
    """Test perform_actions with flags"""
    mocker.patch.object(instrument_control_cli, "VISASerial", new=MockVisaObject)
    mocker.patch.object(instrument_control_cli, "VISATcpip", new=MockVisaObject)
    mocker.patch.object(
        instrument_control_cli,
        "InstrumentControlAuxiliary",
        new=MockInstrumentControlAuxiliary,
    )

    instr = instrument_control_cli.InstrumentControlAuxiliary(MockVisaObject())
    actions = {
        "identification": "get",
        "status_byte": "get",
        "reset": "set",
        "all_errors": "get",
        "self_test": "get",
        "remote_control": "get",
        "output_mode": "get",
        "output_channel": "get",
        "voltage_measure": "get",
        "current_measure": "get",
        "power_measure": "get",
        "voltage_nominal": "get",
        "current_nominal": "get",
        "power_nominal": "get",
        "voltage_target": "get",
        "current_target": "get",
        "power_target": "get",
        "voltage_limit_low": "get",
        "voltage_limit_high": "get",
        "current_limit_low": "get",
        "current_limit_high": "get",
        "power_limit_high": "get",
    }

    assert instrument_control_cli.perform_actions(instr, actions) == None


def test_perform_actions_sets(mocker):
    """Test perform_actions with writes"""
    mocker.patch.object(instrument_control_cli, "VISASerial", new=MockVisaObject)
    mocker.patch.object(instrument_control_cli, "VISATcpip", new=MockVisaObject)
    mocker.patch.object(
        instrument_control_cli,
        "InstrumentControlAuxiliary",
        new=MockInstrumentControlAuxiliary,
    )

    instr = instrument_control_cli.InstrumentControlAuxiliary(MockVisaObject())

    float_value = 1.0
    int_value = 2
    actions = {
        "remote_control": "on",
        "output_mode": "enable",
        "output_channel": int_value,
        "voltage_target": float_value,
        "current_target": float_value,
        "power_target": float_value,
        "voltage_limit_low": float_value,
        "voltage_limit_high": float_value,
        "current_limit_low": float_value,
        "current_limit_high": float_value,
        "power_limit_high": float_value,
    }

    assert instrument_control_cli.perform_actions(instr, actions) == None


def test_perform_actions_unset(mocker):
    mocker.patch.object(instrument_control_cli, "VISASerial", new=MockVisaObject)
    mocker.patch.object(instrument_control_cli, "VISATcpip", new=MockVisaObject)
    mocker.patch.object(
        instrument_control_cli,
        "InstrumentControlAuxiliary",
        new=MockInstrumentControlAuxiliary,
    )

    instr = instrument_control_cli.InstrumentControlAuxiliary(MockVisaObject())

    actions = {
        "remote_control": "off",
        "output_mode": "disable",
    }

    assert instrument_control_cli.perform_actions(instr, actions) == None


@pytest.mark.parametrize(
    "input",
    [
        "command payload",
        "--command payload",
        "__command payload",
    ],
)
def test_parse_user_command(input):
    """Test parse_user_command"""
    assert instrument_control_cli.parse_user_command(input) == {"command": "payload"}


def test_parse_user_command_tag():
    """Test parse_user_command with tags"""
    assert instrument_control_cli.parse_user_command("--input") == {"input": "get"}


# interactive mode not tested
