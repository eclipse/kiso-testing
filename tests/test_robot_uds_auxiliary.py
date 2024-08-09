##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
#
# This source code is copyright protected and proprietary
# to Robert Bosch GmbH. Only those rights that have been
# explicitly granted to you by Robert Bosch GmbH in written
# form may be exercised. All other rights remain with
# Robert Bosch GmbH.
##########################################################################

from time import sleep

import pytest

from pykiso import AuxiliaryInterface
from pykiso.lib.auxiliaries.udsaux.common import UDSCommands
from pykiso.lib.robot_framework.uds_auxiliary import IsoServices, UdsAux, UdsAuxiliary, UdsResponse
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture
def robot_uds_aux(mocker):
    mocker.patch("pykiso.auxiliary.AuxiliaryInterface.start", return_value=None)
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"uds_aux": UdsAux("", tp_layer={}, uds_layer={})},
    )
    return UdsAuxiliary()


@pytest.fixture
def uds_aux(robot_uds_aux):
    return robot_uds_aux._get_aux("uds_aux")


def test_send_uds_raw_with_response(mocker, robot_uds_aux, uds_aux):
    uds_raw_mock = mocker.patch.object(
        uds_aux, "send_uds_raw", return_value=b"\x50\x03"
    )

    response = robot_uds_aux.send_uds_raw(b"\x10\x01", "uds_aux", 6)

    uds_raw_mock.assert_called_with(b"\x10\x01", 6, True)
    assert isinstance(response, list)
    assert response.pop() == 0x03
    assert response.pop() == 0x50


def test_send_uds_raw_with_state(mocker, robot_uds_aux, uds_aux):
    uds_raw_mock = mocker.patch.object(uds_aux, "send_uds_raw", return_value=False)

    response = robot_uds_aux.send_uds_raw(b"\x10\x01", "uds_aux", 6)

    uds_raw_mock.assert_called_with(b"\x10\x01", 6, True)
    assert isinstance(response, bool)


def test_send_uds_config(mocker, robot_uds_aux, uds_aux):
    response = {
        "service": IsoServices.TesterPresent,
        "data": {"suppressResponse": False},
    }
    uds_config_mock = mocker.patch.object(
        uds_aux, "send_uds_config", return_value=response
    )
    message = {"service": "EcuReset", "data": {"parameter": "Soft Reset"}}

    resp = robot_uds_aux.send_uds_config(message, "uds_aux", 6)

    uds_config_mock.assert_called_with(message, 6)
    assert resp == response


def test_get_service_id(robot_uds_aux):
    service = robot_uds_aux.get_service_id("DiagnosticSessionControl")

    assert service == 0x10


def test_get_service_id_exception(robot_uds_aux):

    with pytest.raises(KeyError):
        robot_uds_aux.get_service_id("fake_service")


def test_soft_reset(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_raw")
    uds_aux.uds_config_enable = False

    robot_uds_aux.soft_reset("uds_aux")

    send_mock.assert_called_once()


def test_hard_reset(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_raw")
    uds_aux.uds_config_enable = False

    robot_uds_aux.hard_reset("uds_aux")

    send_mock.assert_called_once()


def test_force_ecu_reset(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_raw")
    uds_aux.uds_config_enable = False

    robot_uds_aux.force_ecu_reset("uds_aux")

    send_mock.assert_called_once()


def test_write_data(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_config")
    uds_aux.uds_config_enable = True

    robot_uds_aux.write_data("Test", b"\x10", "uds_aux")

    send_mock.assert_called_once()


def test_read_data(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_config")
    uds_aux.uds_config_enable = True

    robot_uds_aux.read_data("Test", "uds_aux")

    send_mock.assert_called_once()


def test_check_response_positive(robot_uds_aux, uds_aux):
    with pytest.raises(uds_aux.errors.UnexpectedResponseError):
        robot_uds_aux.check_raw_response_positive(
            UdsResponse([0x7F, 0x22, 0x31]), "uds_aux"
        )


def test_check_response_negative(robot_uds_aux, uds_aux):
    ret = robot_uds_aux.check_raw_response_negative(
        UdsResponse([0x7F, 0x22, 0x31]), "uds_aux"
    )

    assert ret is True


def test_tester_present_sender(mocker, robot_uds_aux, uds_aux):
    send_mock = mocker.patch.object(uds_aux, "send_uds_raw")
    mocker.patch("time.sleep", return_value=None)

    robot_uds_aux.start_tester_present_sender("uds_aux", period=1)
    robot_uds_aux.stop_tester_present_sender("uds_aux")

    send_mock.assert_called_with(
        UDSCommands.TesterPresent.TESTER_PRESENT_NO_RESPONSE, response_required=False
    )
