##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
#
# This source code is copyright protected and proprietary
# to Robert Bosch GmbH. Only those rights that have been
# explicitly granted to you by Robert Bosch GmbH in written
# form may be exercised. All other rights remain with
# Robert Bosch GmbH.
##########################################################################

import logging
from unittest import mock
from unittest.mock import MagicMock

import pytest

from pykiso.lib.auxiliaries.udsaux.common.uds_base_auxiliary import (
    UdsBaseAuxiliary,
)
from pykiso.lib.auxiliaries.udsaux.common.uds_response import (
    NegativeResponseCode,
    UdsResponse,
)


@pytest.fixture(scope="function")
def uds_aux_common_mock(mocker):
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run",
        return_value=None,
    )
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.create_instance",
        return_value=None,
    )
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.delete_instance",
        return_value=None,
    )
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run_command",
        return_value=None,
    )


class TestUdsAuxiliary:
    uds_aux_instance_odx = None
    uds_aux_instance_raw = None

    @pytest.fixture(scope="function")
    def uds_odx_aux_inst(
        self, mocker, uds_aux_common_mock, ccpcan_inst, tmp_uds_config_ini
    ):
        class MockAux(UdsBaseAuxiliary):
            _run_command = mocker.stub(name="_run_command")
            _abort_command = mocker.stub(name="_abort_command")
            _receive_message = mocker.stub(name="_receive_message")

        TestUdsAuxiliary.uds_aux_instance_odx = MockAux(
            ccpcan_inst, tmp_uds_config_ini, "odx"
        )
        return TestUdsAuxiliary.uds_aux_instance_odx

    @pytest.fixture(scope="function")
    def uds_raw_aux_inst(
        self, mocker, uds_aux_common_mock, ccpcan_inst, tmp_uds_config_ini
    ):
        class MockAux(UdsBaseAuxiliary):
            _run_command = mocker.stub(name="_run_command")
            _abort_command = mocker.stub(name="_abort_command")
            _receive_message = mocker.stub(name="_receive_message")

        TestUdsAuxiliary.uds_aux_instance_raw = MockAux(ccpcan_inst, tmp_uds_config_ini)
        return TestUdsAuxiliary.uds_aux_instance_raw

    def test_constructor_odx(self, uds_odx_aux_inst, tmp_uds_config_ini):
        assert uds_odx_aux_inst.is_proxy_capable
        assert str(uds_odx_aux_inst.odx_file_path) == "odx"
        assert uds_odx_aux_inst.config_ini_path == tmp_uds_config_ini

    def test_constructor_raw(self, uds_raw_aux_inst, tmp_uds_config_ini):
        assert uds_raw_aux_inst.is_proxy_capable
        assert uds_raw_aux_inst.odx_file_path is None
        assert uds_raw_aux_inst.config_ini_path == tmp_uds_config_ini

    @pytest.mark.parametrize(
        "channel_name", ["CCPCanCan", "CCVectorCan", "CCSocketCan", "CCProxy"]
    )
    def test_create_auxiliary_instance_odx(
        self, channel_name, mocker, uds_odx_aux_inst
    ):

        uds_mocker = mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.common.uds_base_auxiliary.createUdsConnection",
        )
        uds_odx_aux_inst.receive = MagicMock()
        uds_odx_aux_inst.transmit = MagicMock()

        mocker.patch.object(uds_odx_aux_inst, "uds_config")

        uds_odx_aux_inst.channel.__class__.__name__ = channel_name
        uds_odx_aux_inst._create_auxiliary_instance()

        uds_odx_aux_inst.uds_config.tp.overwrite_receive_method.assert_called_once()
        uds_odx_aux_inst.uds_config.tp.overwrite_transmit_method.assert_called_once()
        uds_mocker.assert_called_once()
        assert uds_odx_aux_inst.uds_config is not None
        assert uds_odx_aux_inst.uds_config_enable

    @mock.patch("pykiso.lib.auxiliaries.udsaux.common.uds_base_auxiliary.Uds")
    def test_create_auxiliary_instance_raw(self, uds_mocker, uds_raw_aux_inst):
        uds_mocker.return_value = "UdsInstanceRaw"

        uds_raw_aux_inst.channel.__class__.__name__ = "CCVectorCan"
        uds_raw_aux_inst._create_auxiliary_instance()

        uds_mocker.assert_called_once()
        assert uds_raw_aux_inst.uds_config == "UdsInstanceRaw"
        assert not uds_raw_aux_inst.uds_config_enable

    def test_create_auxiliary_instance_exception(self, mocker, uds_odx_aux_inst):
        log_mock = mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.common.uds_base_auxiliary.log",
            return_value=logging.getLogger(),
        )

        uds_odx_aux_inst._create_auxiliary_instance()

        log_mock.exception.assert_called_once()

    def test_delete_auxiliary(self, mock_uds_config, uds_odx_aux_inst):
        uds_odx_aux_inst.uds_config = mock_uds_config

        uds_odx_aux_inst.channel.__class__.__name__ = "CCVectorCan"
        uds_odx_aux_inst._create_auxiliary_instance()

        uds_odx_aux_inst._delete_auxiliary_instance()

        uds_odx_aux_inst.uds_config.disconnect.assert_called_once()
