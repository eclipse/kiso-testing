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

from pykiso.lib.auxiliaries.udsaux.common.uds_base_auxiliary import (
    Config,
    Uds,
    UdsBaseAuxiliary,
    warnings,
)


class TestUdsBaseAuxiliary:
    @pytest.fixture
    def aux_inst(self, mocker, cchannel_inst):
        class MockUdsAuxiliary(UdsBaseAuxiliary):
            def __init__(self, *arg, **kwargs):
                config_ini_path = "just for fun"
                super().__init__(cchannel_inst, config_ini_path, *arg, **kwargs)

            _run_command = mocker.stub(name="_run_command")
            _receive_message = mocker.stub(name="_receive_message")
            transmit = mocker.stub(name="transmit")
            receive = mocker.stub(name="receive")

        mocker.patch.object(warnings, "warn")
        return MockUdsAuxiliary()

    def test_init_com_layers_default_values(self, aux_inst):
        aux_inst.req_id = 0x123
        aux_inst.res_id = 0x321

        aux_inst._init_com_layers()
        expected_tp = UdsBaseAuxiliary.DEFAULT_TP_CONFIG
        expected_tp["req_id"] = aux_inst.req_id
        expected_tp["res_id"] = aux_inst.res_id
        assert aux_inst.uds_layer == UdsBaseAuxiliary.DEFAULT_UDS_CONFIG
        assert aux_inst.tp_layer == expected_tp

    def test_create_auxiliary_instance_without_odx(self, mocker, aux_inst):
        mocker.patch(
            "pathlib.Path.exists",
            return_value=False,
        )
        mock_init = mocker.patch.object(Uds, "__init__", return_value=None)
        mock_transmit = mocker.patch.object(Uds, "overwrite_transmit_method")
        mock_receive = mocker.patch.object(Uds, "overwrite_receive_method")
        mock_config = mocker.patch.object(Config, "load_com_layer_config")

        verdict = aux_inst._create_auxiliary_instance()

        aux_inst.channel._cc_open.assert_called_once()
        mock_init.assert_called_once()
        mock_config.assert_called_once()
        mock_transmit.assert_called_with(aux_inst.transmit)
        mock_receive.assert_called_with(aux_inst.receive)
        assert aux_inst.uds_config_enable is False
        assert verdict is True

    def test_create_auxiliary_instance_with_odx(self, mocker, aux_inst):
        mocker.patch(
            "pathlib.Path.exists",
            return_value=True,
        )
        mock_init = mocker.patch.object(Uds, "__init__", return_value=None)
        mock_transmit = mocker.patch.object(Uds, "overwrite_transmit_method")
        mock_receive = mocker.patch.object(Uds, "overwrite_receive_method")
        mock_config = mocker.patch.object(Config, "load_com_layer_config")
        aux_inst.odx_file_path = "something super cool"

        verdict = aux_inst._create_auxiliary_instance()

        aux_inst.channel._cc_open.assert_called_once()
        mock_init.assert_called_once()
        mock_config.assert_called_once()
        mock_transmit.assert_called_with(aux_inst.transmit)
        mock_receive.assert_called_with(aux_inst.receive)
        assert aux_inst.uds_config_enable is True
        assert verdict is True

    def test_create_auxiliary_instance_error(self, mocker, aux_inst):
        mocker.patch.object(Uds, "__init__", side_effect=ValueError)

        verdict = aux_inst._create_auxiliary_instance()

        assert verdict is False

    def test_delete_auxiliary_instance(self, aux_inst):
        verdict = aux_inst._delete_auxiliary_instance()

        aux_inst.channel._cc_close.assert_called_once()
        assert verdict is True

    def test_delete_auxiliary_instance_error(self, mocker, aux_inst):
        mocker.patch.object(aux_inst.channel, "_cc_close", side_effect=ValueError)

        verdict = aux_inst._delete_auxiliary_instance()

        assert verdict is False
