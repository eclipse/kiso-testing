##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_scpi_commands import (
    LibSCPI,
)
from pykiso.lib.robot_framework.instrument_control_auxiliary import (
    InstAux,
    InstrumentControlAuxiliary,
)
from pykiso.test_setup.config_registry import ConfigRegistry


class MockVisaChannel:
    def __init__(self):
        self.resource_name = "messagebased_resource"

    def open(self):
        pass

    def close(self):
        pass

    def write(self, write_command: str, validation: tuple = None):
        return f"response write {write_command}"

    def read(self):
        return "response read"

    def query(self, query_command: str):
        return f"response query {query_command}"


@pytest.fixture
def instrument_aux_instance(
    mocker,
):
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.start", return_value=None
    )
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"inst_aux": InstAux(MockVisaChannel(), "instrument", 1)},
    )
    return InstrumentControlAuxiliary()


def test_write(mocker, instrument_aux_instance):
    write_mock = mocker.patch.object(InstAux, "write", return_value=True)

    instrument_aux_instance.write(
        "SOURce:VOLTage:40", "inst_aux", ("SOURce:VOLTage?", "VALUE{39}")
    )

    write_mock.assert_called_with("SOURce:VOLTage:40", ("SOURce:VOLTage?", "VALUE{39}"))


def test_read(mocker, instrument_aux_instance):
    read_mock = mocker.patch.object(InstAux, "read", return_value=True)

    instrument_aux_instance.read("inst_aux")

    read_mock.assert_called_once()


def test_query(mocker, instrument_aux_instance):
    query_mock = mocker.patch.object(InstAux, "query", return_value=True)

    instrument_aux_instance.query("*IDN?", "inst_aux")

    query_mock.assert_called_with("*IDN?")


def test_get_identification(mocker, instrument_aux_instance):
    ident_mock = mocker.patch.object(LibSCPI, "get_identification", return_value=True)

    instrument_aux_instance.get_identification("inst_aux")

    ident_mock.assert_called_once()


def test_get_status_byte(mocker, instrument_aux_instance):
    status_mock = mocker.patch.object(LibSCPI, "get_status_byte", return_value=True)

    instrument_aux_instance.get_status_byte("inst_aux")

    status_mock.assert_called_once()


def test_get_all_errors(mocker, instrument_aux_instance):
    errors_mock = mocker.patch.object(LibSCPI, "get_all_errors", return_value=True)

    instrument_aux_instance.get_all_errors("inst_aux")

    errors_mock.assert_called_once()


def test_reset(mocker, instrument_aux_instance):
    reset_mock = mocker.patch.object(LibSCPI, "reset", return_value=True)

    instrument_aux_instance.reset("inst_aux")

    reset_mock.assert_called_once()


def test_self_test(mocker, instrument_aux_instance):
    test_mock = mocker.patch.object(LibSCPI, "self_test", return_value=True)

    instrument_aux_instance.self_test("inst_aux")

    test_mock.assert_called_once()


def test_get_remote_control_state(mocker, instrument_aux_instance):
    remote_state_mock = mocker.patch.object(
        LibSCPI, "get_remote_control_state", return_value=True
    )

    instrument_aux_instance.get_remote_control_state("inst_aux")

    remote_state_mock.assert_called_once()


def test_set_remote_control_on(mocker, instrument_aux_instance):
    remote_on_mock = mocker.patch.object(
        LibSCPI, "set_remote_control_on", return_value=True
    )

    instrument_aux_instance.set_remote_control_on("inst_aux")

    remote_on_mock.assert_called_once()


def test_set_remote_control_off(mocker, instrument_aux_instance):
    remote_off_mock = mocker.patch.object(
        LibSCPI, "set_remote_control_off", return_value=True
    )

    instrument_aux_instance.set_remote_control_off("inst_aux")

    remote_off_mock.assert_called_once()


def test_get_output_channel(mocker, instrument_aux_instance):
    output_channel_mock = mocker.patch.object(
        LibSCPI, "get_output_channel", return_value=True
    )

    instrument_aux_instance.get_output_channel("inst_aux")

    output_channel_mock.assert_called_once()


def test_set_output_channel(mocker, instrument_aux_instance):
    set_channel_mock = mocker.patch.object(
        LibSCPI, "set_output_channel", return_value=True
    )

    instrument_aux_instance.set_output_channel(1, "inst_aux")

    set_channel_mock.assert_called_with(1)


def test_get_output_state(mocker, instrument_aux_instance):
    output_state_mock = mocker.patch.object(
        LibSCPI, "get_output_state", return_value=True
    )

    instrument_aux_instance.get_output_state("inst_aux")

    output_state_mock.assert_called_once()


def test_enable_output(mocker, instrument_aux_instance):
    enable_mock = mocker.patch.object(LibSCPI, "enable_output", return_value=True)

    instrument_aux_instance.enable_output("inst_aux")

    enable_mock.assert_called_once()


def test_disable_output(mocker, instrument_aux_instance):
    disable_mock = mocker.patch.object(LibSCPI, "disable_output", return_value=True)

    instrument_aux_instance.disable_output("inst_aux")

    disable_mock.assert_called_once()


def test_get_nominal_voltage(mocker, instrument_aux_instance):
    voltage_mock = mocker.patch.object(
        LibSCPI, "get_nominal_voltage", return_value=True
    )

    instrument_aux_instance.get_nominal_voltage("inst_aux")

    voltage_mock.assert_called_once()


def test_get_nominal_current(mocker, instrument_aux_instance):
    current_mock = mocker.patch.object(
        LibSCPI, "get_nominal_current", return_value=True
    )

    instrument_aux_instance.get_nominal_current("inst_aux")

    current_mock.assert_called_once()


def test_get_nominal_power(mocker, instrument_aux_instance):
    power_mock = mocker.patch.object(LibSCPI, "get_nominal_power", return_value=True)

    instrument_aux_instance.get_nominal_power("inst_aux")

    power_mock.assert_called_once()


def test_measure_voltage(mocker, instrument_aux_instance):
    voltage_mock = mocker.patch.object(LibSCPI, "measure_voltage", return_value=True)

    instrument_aux_instance.measure_voltage("inst_aux")

    voltage_mock.assert_called_once()


def test_measure_current(mocker, instrument_aux_instance):
    current_mock = mocker.patch.object(LibSCPI, "measure_current", return_value=True)

    instrument_aux_instance.measure_current("inst_aux")

    current_mock.assert_called_once()


def test_measure_power(mocker, instrument_aux_instance):
    power_mock = mocker.patch.object(LibSCPI, "measure_power", return_value=True)

    instrument_aux_instance.measure_power("inst_aux")

    power_mock.assert_called_once()


def test_get_target_voltage(mocker, instrument_aux_instance):
    voltage_mock = mocker.patch.object(LibSCPI, "get_target_voltage", return_value=True)

    instrument_aux_instance.get_target_voltage("inst_aux")

    voltage_mock.assert_called_once()


def test_get_target_current(mocker, instrument_aux_instance):
    current_mock = mocker.patch.object(LibSCPI, "get_target_current", return_value=True)

    instrument_aux_instance.get_target_current("inst_aux")

    current_mock.assert_called_once()


def test_get_target_power(mocker, instrument_aux_instance):
    power_mock = mocker.patch.object(LibSCPI, "get_target_power", return_value=True)

    instrument_aux_instance.get_target_power("inst_aux")

    power_mock.assert_called_once()


def test_set_target_voltage(mocker, instrument_aux_instance):
    voltage_mock = mocker.patch.object(LibSCPI, "set_target_voltage", return_value=True)

    instrument_aux_instance.set_target_voltage(40.0, "inst_aux")

    voltage_mock.assert_called_with(40.0)


def test_set_target_current(mocker, instrument_aux_instance):
    current_mock = mocker.patch.object(LibSCPI, "set_target_current", return_value=True)

    instrument_aux_instance.set_target_current(1.0, "inst_aux")

    current_mock.assert_called_with(1.0)


def test_set_target_power(mocker, instrument_aux_instance):
    power_mock = mocker.patch.object(LibSCPI, "set_target_power", return_value=True)

    instrument_aux_instance.set_target_power(2.0, "inst_aux")

    power_mock.assert_called_with(2.0)


def test_get_voltage_limit_low(mocker, instrument_aux_instance):
    voltage_low_mock = mocker.patch.object(
        LibSCPI, "get_voltage_limit_low", return_value=True
    )

    instrument_aux_instance.get_voltage_limit_low("inst_aux")

    voltage_low_mock.assert_called_once()


def test_get_voltage_limit_high(mocker, instrument_aux_instance):
    voltage_high_mock = mocker.patch.object(
        LibSCPI, "get_voltage_limit_high", return_value=True
    )

    instrument_aux_instance.get_voltage_limit_high("inst_aux")

    voltage_high_mock.assert_called_once()


def test_get_current_limit_low(mocker, instrument_aux_instance):
    current_low_mock = mocker.patch.object(
        LibSCPI, "get_current_limit_low", return_value=True
    )

    instrument_aux_instance.get_current_limit_low("inst_aux")

    current_low_mock.assert_called_once()


def test_get_current_limit_high(mocker, instrument_aux_instance):
    current_high_mock = mocker.patch.object(
        LibSCPI, "get_current_limit_high", return_value=True
    )

    instrument_aux_instance.get_current_limit_high("inst_aux")

    current_high_mock.assert_called_once()


def test_get_power_limit_high(mocker, instrument_aux_instance):
    power_high_mock = mocker.patch.object(
        LibSCPI, "get_power_limit_high", return_value=True
    )

    instrument_aux_instance.get_power_limit_high("inst_aux")

    power_high_mock.assert_called_once()


def test_set_voltage_limit_low(mocker, instrument_aux_instance):
    voltage_low_mock = mocker.patch.object(
        LibSCPI, "set_voltage_limit_low", return_value=True
    )

    instrument_aux_instance.set_voltage_limit_low(0.0, "inst_aux")

    voltage_low_mock.assert_called_with(0.0)


def test_set_voltage_limit_high(mocker, instrument_aux_instance):
    voltage_high_mock = mocker.patch.object(
        LibSCPI, "set_voltage_limit_high", return_value=True
    )

    instrument_aux_instance.set_voltage_limit_high(36.00, "inst_aux")

    voltage_high_mock.assert_called_with(36.00)


def test_set_current_limit_low(mocker, instrument_aux_instance):
    current_low_mock = mocker.patch.object(
        LibSCPI, "set_current_limit_low", return_value=True
    )

    instrument_aux_instance.set_current_limit_low(0.00, "inst_aux")

    current_low_mock.assert_called_with(0.00)


def test_set_current_limit_high(mocker, instrument_aux_instance):
    current_high_mock = mocker.patch.object(
        LibSCPI, "set_current_limit_high", return_value=True
    )

    instrument_aux_instance.set_current_limit_high(5.00, "inst_aux")

    current_high_mock.assert_called_with(5.00)


def test_set_power_limit_high(mocker, instrument_aux_instance):
    power_high_mock = mocker.patch.object(
        LibSCPI, "set_power_limit_high", return_value=True
    )

    instrument_aux_instance.set_power_limit_high(5.00, "inst_aux")

    power_high_mock.assert_called_with(5.00)
