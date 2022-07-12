##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import logging

import pytest
import pyvisa

from pykiso.lib.connectors import cc_visa
from pykiso.message import Message

constructor_params_serial = {"serial_port": 4, "baud_rate": 9600}
constructor_params_tcpip = {
    "ip_address": "10.10.10.10",
    "protocol": "TCPIP",
}
scpi_cmds = {
    "example": "EXAMPLE:CMD",
    "trigger_timeout_error": "TIMEOUT_ERR_CMD",
    "trigger_invalid_session_error": "INVALID_SESSION_ERR_CMD",
    "trigger_other_error": "OTHER_ERR_CND",
}


class MockSerialInstrument:
    """Class used to mock pyvisa.resources.serial.SerialInstrument class"""

    def __init__(self, serial_port: int, baud_rate: int = 9600, **kwargs):
        self.resource_name = f"ASRL{serial_port}::INSTR"
        self.baud_rate = baud_rate

    def read(self):
        return "read response"

    def write(self, write_command):
        return f"command {write_command} write response"

    def query(self, query_command):
        if query_command == scpi_cmds["trigger_timeout_error"]:
            raise pyvisa.errors.VisaIOError()
        elif query_command == scpi_cmds["trigger_invalid_session_error"]:
            raise pyvisa.errors.InvalidSession()
        elif query_command == scpi_cmds["trigger_other_error"]:
            raise ConnectionError()
        else:
            return f"command {query_command} query response"


class MockTcpipInstrument:
    """Class used to mock pyvisa.resources.tcpip.TCPIPInstrument() class"""

    def __init__(self, ip_address: str, **kwargs):
        self.resource_name = f"TCPIP::{ip_address}::INSTR"

    def read(self):
        return "read response"

    def write(self, write_command):
        return f"command {write_command} write response"

    def query(self, query_command):
        if query_command == scpi_cmds["trigger_timeout_error"]:
            raise pyvisa.errors.VisaIOError("Timeout error")
        elif query_command == scpi_cmds["trigger_invalid_session_error"]:
            raise pyvisa.errors.InvalidSession("Invalid session error")
        elif query_command == scpi_cmds["trigger_other_error"]:
            raise ConnectionError("Other error")
        else:
            return f"command {query_command} query response"


class MockResourceManager:
    """Class used to stub pyvisa.ResourceManager() class"""

    def __init__(self, visalib):
        self.visalib = visalib
        self.resources = ["ASRL1::INSTR", "ASRL2::INSTR"]
        self.opened_resources = [f"ASRL1::INSTR"]

    def open_resource(self, resource_name: str):
        self.list_opened_resources.append(resource_name)

    def list_resources(self):
        return self.resources

    def list_opened_resources(self):
        return self.opened_resources


# Test of VisaChannel (sometimes using VisaSerial mock)
def test_visa_channel_abstract():
    """ensure VISAChannel is not instantiable"""
    with pytest.raises(TypeError):
        c = cc_visa.VISAChannel("will fail")


@pytest.mark.parametrize(
    "constructor_params_serial",
    [
        constructor_params_serial,
    ],
)
def test_cc_close(constructor_params_serial):
    visa_inst = cc_visa.VISASerial(constructor_params_serial)
    assert visa_inst._cc_close() is None


@pytest.mark.parametrize(
    "constructor_params_serial, raw_value, expected_return",
    [
        (constructor_params_serial, True, {"msg": b"read response"}),
        (constructor_params_serial, False, {"msg": "read response"}),
    ],
)
def test_cc_receive(mocker, constructor_params_serial, raw_value, expected_return):
    visa_inst = cc_visa.VISASerial(constructor_params_serial)
    mocker.patch.object(visa_inst, "resource", new=MockSerialInstrument(serial_port=3))
    message_received = visa_inst._cc_receive()
    if raw_value:
        message_received["msg"] = message_received["msg"].encode()

    assert message_received == expected_return


@pytest.mark.parametrize(
    "constructor_params_serial, scpi_cmds",
    [
        (
            constructor_params_serial,
            scpi_cmds,
        )
    ],
)
def test__process_request(mocker, constructor_params_serial, scpi_cmds, caplog):
    visa_inst = cc_visa.VISASerial(constructor_params_serial)
    mocker.patch.object(visa_inst, "resource", new=MockSerialInstrument(serial_port=3))
    # Test when command is normally processed
    assert visa_inst._process_request(
        request="query", request_data=scpi_cmds["example"]
    ) == {"msg": f"command {scpi_cmds['example']} query response"}

    # Test when timeout error occurs
    assert visa_inst._process_request(
        request="query", request_data=scpi_cmds["trigger_timeout_error"]
    ) == {"msg": ""}

    # Test when invalid session error occurs
    assert visa_inst._process_request(
        request="query", request_data=scpi_cmds["trigger_invalid_session_error"]
    ) == {"msg": ""}

    # Test when timeout error occurs
    assert visa_inst._process_request(
        request="query", request_data=scpi_cmds["trigger_other_error"]
    ) == {"msg": ""}

    with caplog.at_level(logging.WARNING):
        assert visa_inst._process_request(
            request="Test", request_data=scpi_cmds["trigger_other_error"]
        ) == {"msg": ""}
    assert "Unknown request 'Test'!" in caplog.text


@pytest.mark.parametrize(
    "constructor_params_serial, scpi_cmds",
    [
        (
            constructor_params_serial,
            scpi_cmds,
        )
    ],
)
def test__cc_send(mocker, constructor_params_serial, scpi_cmds):
    visa_inst = cc_visa.VISASerial(constructor_params_serial)
    mocker.patch.object(visa_inst, "resource", new=MockSerialInstrument(serial_port=3))

    # Test with string input
    assert visa_inst._cc_send(scpi_cmds["example"]) is None

    # Test with bytes input
    assert visa_inst._cc_send(b"example".decode()) is None


@pytest.mark.parametrize(
    "constructor_params_serial, scpi_cmds",
    [
        (
            constructor_params_serial,
            scpi_cmds,
        )
    ],
)
def test_query(mocker, constructor_params_serial, scpi_cmds):
    visa_inst = cc_visa.VISASerial(constructor_params_serial)
    mocker.patch.object(visa_inst, "resource", new=MockSerialInstrument(serial_port=3))
    # Test when command is normally processed
    assert visa_inst.query(query_command=scpi_cmds["example"]) == {
        "msg": f"command {scpi_cmds['example']} query response"
    }

    # Test when timeout error occurs
    assert visa_inst.query(
        query_command=scpi_cmds["trigger_invalid_session_error"]
    ) == {"msg": ""}

    # Test when invalid session error occurs
    assert visa_inst.query(query_command=scpi_cmds["trigger_timeout_error"]) == {
        "msg": ""
    }

    # Test when timeout error occurs
    assert visa_inst.query(query_command=scpi_cmds["trigger_other_error"]) == {
        "msg": ""
    }


# Test of VisaSerial and VisaTcpip connector


@pytest.mark.parametrize(
    "constructor_params_serial, expected_config_serial, constructor_params_tcpip, expected_config_tcpip",
    [
        (
            constructor_params_serial,
            {
                "resource_name": f"ASRL{constructor_params_serial['serial_port']}::INSTR",
                "baud_rate": constructor_params_serial["baud_rate"],
            },
            constructor_params_tcpip,
            {
                "resource_name": f"TCPIP::{constructor_params_tcpip['ip_address']}::{constructor_params_tcpip['protocol']}",
                "protocol": constructor_params_tcpip["protocol"],
            },
        ),
    ],
)
def test_constructor(
    constructor_params_serial,
    expected_config_serial,
    constructor_params_tcpip,
    expected_config_tcpip,
):
    ## Test VisaSerial connector __init__
    param = constructor_params_serial.values()

    visa_inst = cc_visa.VISASerial(*param)

    assert visa_inst.resource_name == expected_config_serial["resource_name"]
    assert visa_inst.baud_rate == expected_config_serial["baud_rate"]
    assert isinstance(visa_inst.resource, pyvisa.resources.serial.SerialInstrument)
    assert isinstance(visa_inst.ResourceManager, pyvisa.highlevel.ResourceManager)

    ## Test VisaTcpip connector __init__
    param = constructor_params_tcpip.values()

    visa_inst = cc_visa.VISATcpip(*param)

    assert visa_inst.resource_name == expected_config_tcpip["resource_name"]
    assert visa_inst.protocol == expected_config_tcpip["protocol"]
    assert isinstance(visa_inst.resource, pyvisa.resources.tcpip.TCPIPInstrument)
    assert isinstance(visa_inst.ResourceManager, pyvisa.highlevel.ResourceManager)


@pytest.mark.parametrize(
    "serial_port, constructor_params_tcpip",
    [
        (
            {"available_and_opened": 1, "available": 2, "unavailable": 3},
            constructor_params_tcpip,
        ),
    ],
)
def test_cc_open(mocker, serial_port, constructor_params_tcpip):
    """Test open instrument"""
    ## Test VisaSerial connector
    # Test open an available instrument
    visa_inst = cc_visa.VISASerial(serial_port["available"])

    mocker.patch.object(
        visa_inst.ResourceManager,
        "list_resources",
        return_value=[
            MockSerialInstrument(
                serial_port=serial_port["available_and_opened"]
            ).resource_name,
            MockSerialInstrument(serial_port=serial_port["available"]).resource_name,
        ],
    )
    mocker.patch.object(
        visa_inst.ResourceManager,
        "list_opened_resources",
        return_value=[
            MockSerialInstrument(serial_port=serial_port["available_and_opened"])
        ],
    )
    mocker.patch.object(visa_inst.ResourceManager, "open_resource")

    assert visa_inst._cc_open() is None

    # Test open an available but already opened instrument
    visa_inst = cc_visa.VISASerial(serial_port["available_and_opened"])
    with pytest.raises(ConnectionRefusedError) as e:
        visa_inst._cc_open()
    assert (
        str(e.value)
        == f"The resource named {visa_inst.resource_name} is opened and cannot be opened again."
    )

    # Test open an unavailable instrument
    visa_inst = cc_visa.VISASerial(serial_port["unavailable"])
    with pytest.raises(ConnectionRefusedError) as e:
        visa_inst._cc_open()
    assert (
        str(e.value)
        == f"The resource named {visa_inst.resource_name} is unavailable and cannot be opened."
    )

    # Test of VisaTcpip connector open
    param = constructor_params_tcpip.values()

    visa_inst = cc_visa.VISATcpip(*param)

    ## Test open an available instrument
    assert visa_inst._cc_open() is None
