##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.aux_interface import RobotAuxInterface


@pytest.fixture
def dummy_aux_instance():
    class MyAux:
        def __init__(self):
            self.channel = True
            self.flash = True

    return MyAux


@pytest.fixture
def aux_interface_instance(mocker, dummy_aux_instance):
    auxes = {"dummy_aux_1": dummy_aux_instance(), "dummy_aux_2": dummy_aux_instance()}
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value=auxes,
    )
    interface_inst = RobotAuxInterface(dummy_aux_instance)
    return interface_inst, auxes


def test_get_aux(aux_interface_instance, dummy_aux_instance):
    inst, auxes = aux_interface_instance
    aux = inst._get_aux("dummy_aux_2")

    assert isinstance(aux, dummy_aux_instance)
    assert aux == auxes["dummy_aux_2"]


def test_get_aux_raise_exception(aux_interface_instance):
    inst, _ = aux_interface_instance

    with pytest.raises(KeyError):
        aux = inst._get_aux("not_existing_one")


def test_get_aux_connectors(aux_interface_instance):
    inst, _ = aux_interface_instance
    channel = inst._get_aux_connectors("dummy_aux_1")

    assert channel


def test_get_aux_flasher(aux_interface_instance):
    inst, _ = aux_interface_instance
    flash = inst._get_aux_flasher("dummy_aux_2")

    assert flash
