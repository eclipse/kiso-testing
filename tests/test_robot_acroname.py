##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.acroname_auxiliary import (
    AcroAux,
    AcronameAuxiliary,
)


@pytest.fixture
def acroname_aux_instance(
    mocker,
):

    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"acroname_aux": AcroAux()},
    )
    return AcronameAuxiliary()


def test_set_port_enable(mocker, acroname_aux_instance):
    set_port_enable_mock = mocker.patch.object(
        AcroAux, "set_port_enable", return_value=True
    )

    acroname_aux_instance.set_port_enable("acroname_aux", 1)
    set_port_enable_mock.assert_called_with(1)


def test_set_port_disable(mocker, acroname_aux_instance):
    set_port_disable_mock = mocker.patch.object(
        AcroAux, "set_port_disable", return_value=True
    )

    acroname_aux_instance.set_port_disable("acroname_aux", 1)
    set_port_disable_mock.assert_called_with(1)


def test_get_port_current(mocker, acroname_aux_instance):
    get_port_current_mock = mocker.patch.object(
        AcroAux, "get_port_current", return_value=500
    )

    acroname_aux_instance.get_port_current("acroname_aux", 1, "mA")
    get_port_current_mock.assert_called_with(1, "mA")


def test_get_port_voltage(mocker, acroname_aux_instance):
    get_port_voltage_mock = mocker.patch.object(
        AcroAux, "get_port_voltage", return_value=500
    )

    acroname_aux_instance.get_port_voltage("acroname_aux", 1, "mv")
    get_port_voltage_mock.assert_called_with(1, "mv")


def test_get_port_current_limit(mocker, acroname_aux_instance):
    get_port_current_limit_mock = mocker.patch.object(
        AcroAux, "get_port_current_limit", return_value=500
    )

    acroname_aux_instance.get_port_current_limit("acroname_aux", 1, "mA")
    get_port_current_limit_mock.assert_called_with(1, "mA")


def test_set_port_current_limit(mocker, acroname_aux_instance):
    set_port_current_limit_mock = mocker.patch.object(
        AcroAux, "set_port_current_limit", return_value=500
    )

    acroname_aux_instance.set_port_current_limit("acroname_aux", 1, 0.5, "A")
    set_port_current_limit_mock.assert_called_with(1, 0.5, "A")
