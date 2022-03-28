##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
#
# This source code is copyright protected and proprietary
# to Robert Bosch GmbH. Only those rights that have been
# explicitly granted to you by Robert Bosch GmbH in written
# form may be exercised. All other rights remain with
# Robert Bosch GmbH.
##########################################################################

import pytest

from pykiso import AuxiliaryInterface
from pykiso.lib.robot_framework.uds_auxiliary import (
    IsoServices,
    UdsAux,
    UdsAuxiliary,
    UdsResponse,
)
from pykiso.test_setup.config_registry import ConfigRegistry


def create_config():
    cfg = """
[can]
interface=peak
canfd=True
baudrate=500000
data_baudrate=2000000
defaultReqId=0xAB
defaultResId=0xAC
    """
    return cfg


@pytest.fixture
def tmp_config_ini(tmp_path):
    uds_folder = tmp_path / "fake_robot_uds"
    uds_folder.mkdir()
    config_ini = uds_folder / "_config.ini"
    config_ini.write_text(create_config())
    import logging

    logging.error(config_ini)
    return config_ini


@pytest.fixture(scope="function")
def robot_uds_aux(mocker, tmp_config_ini):
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run", return_value=None
    )
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"uds_aux": UdsAux("", tmp_config_ini)},
    )
    return UdsAuxiliary()


@pytest.fixture(scope="function")
def uds_aux(robot_uds_aux):
    return robot_uds_aux._get_aux("uds_aux")


def test_send_uds_raw_with_response(mocker, robot_uds_aux, uds_aux):
    uds_raw_mock = mocker.patch.object(
        uds_aux, "send_uds_raw", return_value=b"\x50\x03"
    )

    response = robot_uds_aux.send_uds_raw(b"\x10\x01", "uds_aux", 6)

    uds_raw_mock.assert_called_with(b"\x10\x01", 6)
    assert isinstance(response, list)
    assert response.pop() == 0x03
    assert response.pop() == 0x50


def test_send_uds_raw_with_state(mocker, robot_uds_aux, uds_aux):
    uds_raw_mock = mocker.patch.object(uds_aux, "send_uds_raw", return_value=False)

    response = robot_uds_aux.send_uds_raw(b"\x10\x01", "uds_aux", 6)

    uds_raw_mock.assert_called_with(b"\x10\x01", 6)
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
