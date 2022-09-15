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
from time import sleep
from unittest import mock

import pytest

from pykiso.lib.auxiliaries.udsaux.common import UDSCommands
from pykiso.lib.auxiliaries.udsaux.common.uds_response import (
    NegativeResponseCode,
    UdsResponse,
)
from pykiso.lib.auxiliaries.udsaux.uds_auxiliary import UdsAuxiliary


class TestUdsAuxiliary:
    uds_aux_instance_odx = None
    uds_aux_instance_odx_v = None
    uds_aux_instance_raw = None

    @pytest.fixture(scope="function")
    def uds_odx_aux_inst(self, mocker, ccpcan_inst, tmp_uds_config_ini):

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
        mocker.patch(
            "pathlib.Path.exists",
            return_value=True,
        )
        TestUdsAuxiliary.uds_aux_instance_odx = UdsAuxiliary(
            ccpcan_inst, tmp_uds_config_ini, "odx"
        )
        return TestUdsAuxiliary.uds_aux_instance_odx

    @pytest.fixture(scope="function")
    def uds_odx_aux_inst_v(self, mocker, ccvector_inst, tmp_uds_config_ini):

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
        TestUdsAuxiliary.uds_aux_instance_odx_v = UdsAuxiliary(
            ccvector_inst, tmp_uds_config_ini, "odx"
        )
        return TestUdsAuxiliary.uds_aux_instance_odx_v

    @pytest.fixture(scope="function")
    def uds_raw_aux_inst(self, mocker, ccpcan_inst, tmp_uds_config_ini):
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
        TestUdsAuxiliary.uds_aux_instance_raw = UdsAuxiliary(
            ccpcan_inst, tmp_uds_config_ini
        )
        return TestUdsAuxiliary.uds_aux_instance_raw

    def test_constructor_odx(self, uds_odx_aux_inst, tmp_uds_config_ini):
        assert uds_odx_aux_inst.is_proxy_capable
        assert str(uds_odx_aux_inst.odx_file_path) == "odx"
        assert uds_odx_aux_inst.tp_waiting_time == 0.010

    def test_constructor_raw(self, uds_raw_aux_inst, tmp_uds_config_ini):
        assert uds_raw_aux_inst.is_proxy_capable
        assert uds_raw_aux_inst.odx_file_path is None
        assert uds_raw_aux_inst.tp_waiting_time == 0.010

    def test_send_uds_raw(self, mock_uds_config, uds_odx_aux_inst):
        mock_uds_config.send.return_value = [0x50, 0x03]
        uds_odx_aux_inst.uds_config = mock_uds_config
        uds_odx_aux_inst.POSITIVE_RESPONSE_OFFSET = 0x40
        uds_odx_aux_inst.tp_waiting_time = 0.020

        resp = uds_odx_aux_inst.send_uds_raw([0x10, 0x03])

        mock_uds_config.send.assert_called_with(
            [0x10, 0x03],
            responseRequired=True,
            tpWaitTime=uds_odx_aux_inst.tp_waiting_time,
        )
        assert resp == [0x50, 0x03]

    def test_send_uds_raw_no_response_required(self, mock_uds_config, uds_odx_aux_inst):
        mock_uds_config.send.return_value = None
        uds_odx_aux_inst.uds_config = mock_uds_config

        resp = uds_odx_aux_inst.send_uds_raw([0x10, 0x03], response_required=False)

        assert resp == True

    def test_send_uds_raw_resp_empty_list(self, mock_uds_config, uds_odx_aux_inst):
        mock_uds_config.send.return_value = []
        uds_odx_aux_inst.uds_config = mock_uds_config
        uds_odx_aux_inst.POSITIVE_RESPONSE_OFFSET = 0x40

        resp = uds_odx_aux_inst.send_uds_raw([0x10, 0x03])

        assert resp == []

    def test_send_uds_raw_no_response(self, mock_uds_config, uds_odx_aux_inst):
        mock_uds_config.send.return_value = None
        uds_odx_aux_inst.uds_config = mock_uds_config

        with pytest.raises(uds_odx_aux_inst.errors.ResponseNotReceivedError):
            uds_odx_aux_inst.send_uds_raw([0x10, 0x03])

    def test_send_uds_raw_exception(self, mocker, mock_uds_config, uds_odx_aux_inst):
        log_mock = mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.uds_auxiliary.log",
            return_value=logging.getLogger(),
        )
        mock_uds_config.send.side_effect = Exception()
        uds_odx_aux_inst.uds_config = mock_uds_config

        uds_odx_aux_inst.send_uds_raw([0x10, 0x03])

        log_mock.exception.assert_called_once()

    def test_check_raw_negative_response(self, caplog, uds_odx_aux_inst):
        with caplog.at_level(logging.ERROR):
            ret = uds_odx_aux_inst.check_raw_response_negative(
                UdsResponse([0x7F, 0x10, 0x22])
            )
        assert "Negative response with : CONDITIONS_NOT_CORRECT"
        assert ret is True

    def test_check_raw_positive_response(self, uds_odx_aux_inst):
        ret = uds_odx_aux_inst.check_raw_response_positive(
            UdsResponse([0x51, 0x10, 0x22])
        )
        assert ret is True

    def test_check_response_positive_got_negative_instead(self, uds_raw_aux_inst):
        with pytest.raises(uds_raw_aux_inst.errors.UnexpectedResponseError):
            uds_raw_aux_inst.check_raw_response_positive(
                UdsResponse([0x7F, 0x22, 0x31])
            )

    @mock.patch("pykiso.lib.auxiliaries.udsaux.uds_auxiliary.get_uds_service")
    def test_send_uds_config_exception_1(
        self, get_uds_srv_mock, mocker, uds_odx_aux_inst
    ):
        log_mock = mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.uds_auxiliary.log",
            return_value=logging.getLogger(),
        )

        get_uds_srv_mock.return_value = None
        cfg_data = {}

        uds_odx_aux_inst.channel.__class__.__name__ = "CCPCanCan"
        uds_odx_aux_inst._create_auxiliary_instance()
        uds_odx_aux_inst.send_uds_config(cfg_data)

        log_mock.exception.assert_called_once()

    @mock.patch("pykiso.lib.auxiliaries.udsaux.uds_auxiliary.get_uds_service")
    def test_send_uds_config_exception_2(
        self, get_uds_srv_mock, mocker, mock_uds_config, uds_odx_aux_inst
    ):
        log_mock = mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.uds_auxiliary.log",
            return_value=logging.getLogger(),
        )
        get_uds_srv_mock.return_value = "rdbi"

        cfg_data = {}

        mock_uds_config.rdbi.side_effect = 1

        uds_odx_aux_inst.channel.__class__.__name__ = "CCPCanCan"
        uds_odx_aux_inst._create_auxiliary_instance()
        uds_odx_aux_inst.uds_config = mock_uds_config

        uds_odx_aux_inst.send_uds_config(cfg_data)

        log_mock.exception.assert_called_once()

    @mock.patch("pykiso.lib.auxiliaries.udsaux.uds_auxiliary.get_uds_service")
    def test_send_uds_config(self, get_uds_srv_mock, mock_uds_config, uds_odx_aux_inst):
        get_uds_srv_mock.return_value = "rdbi"

        cfg_data = {"service": "", "data": {}}
        mock_uds_config.rdbi.return_value = {"data": "DATA"}

        uds_odx_aux_inst.channel.__class__.__name__ = "CCPCanCan"
        uds_odx_aux_inst._create_auxiliary_instance()
        uds_odx_aux_inst.uds_config = mock_uds_config

        ret = uds_odx_aux_inst.send_uds_config(cfg_data)

        assert ret == {"data": "DATA"}

    @mock.patch("pykiso.lib.auxiliaries.udsaux.uds_auxiliary.get_uds_service")
    def test_send_uds_config_no_odx(self, mock_uds_config, uds_odx_aux_inst):
        cfg_data = {"service": "", "data": {}}
        uds_odx_aux_inst.uds_config = mock_uds_config
        uds_odx_aux_inst.uds_config_enable = False

        ret = uds_odx_aux_inst.send_uds_config(cfg_data)

        assert ret is False

    @mock.patch("pykiso.lib.auxiliaries.udsaux.uds_auxiliary.get_uds_service")
    def test_send_uds_config_no_response_expected(
        self, get_uds_srv_mock, mock_uds_config, uds_odx_aux_inst
    ):
        get_uds_srv_mock.return_value = "rdbi"

        cfg_data = {"service": "", "data": {}}
        mock_uds_config.rdbi.return_value = None
        uds_odx_aux_inst.uds_config = mock_uds_config
        uds_odx_aux_inst.uds_config_enable = True

        ret = uds_odx_aux_inst.send_uds_config(cfg_data)

        assert ret

    def test_soft_reset(self, uds_raw_aux_inst, mocker):
        send_mock = mocker.patch.object(
            uds_raw_aux_inst, "send_uds_raw", return_value=[0x50, 0x03]
        )
        uds_raw_aux_inst.uds_config_enable = False

        uds_raw_aux_inst.soft_reset()

        send_mock.assert_called_once()

    def test_soft_reset_via_uds_config(self, uds_raw_aux_inst, mocker):
        send_mock = mocker.patch.object(
            uds_raw_aux_inst, "send_uds_config", return_value=[0x50, 0x03]
        )
        uds_raw_aux_inst.uds_config_enable = True

        uds_raw_aux_inst.soft_reset()

        send_mock.assert_called_once()

    def test_hard_reset(self, uds_raw_aux_inst, mocker):
        send_mock = mocker.patch.object(
            uds_raw_aux_inst, "send_uds_raw", return_value=[0x50, 0x01]
        )
        uds_raw_aux_inst.uds_config_enable = False

        uds_raw_aux_inst.hard_reset()
        send_mock.assert_called_once()

    def test_force_ecu_reset(self, uds_raw_aux_inst, mocker):
        send_mock = mocker.patch.object(
            uds_raw_aux_inst, "send_uds_raw", return_value=[0x50, 0x02]
        )

        uds_raw_aux_inst.force_ecu_reset()

        send_mock.assert_called_once()

    def test_force_ecu_reset_via_uds_config(self, uds_raw_aux_inst, mocker):
        send_mock = mocker.patch.object(
            uds_raw_aux_inst, "send_uds_config", return_value=[0x50, 0x01]
        )
        uds_raw_aux_inst.uds_config_enable = True

        uds_raw_aux_inst.force_ecu_reset()

        send_mock.assert_called_once()

    @pytest.mark.parametrize("uds_config, mock_count", [(True, 1), (False, 0)])
    def test_read_data(self, uds_raw_aux_inst, mocker, uds_config, mock_count):
        send_mock = mocker.patch.object(uds_raw_aux_inst, "send_uds_config")
        uds_raw_aux_inst.uds_config_enable = uds_config

        uds_raw_aux_inst.read_data(parameter="test")
        assert send_mock.call_count == mock_count

    @pytest.mark.parametrize("uds_config, mock_count", [(True, 1), (False, 0)])
    def test_write_data(self, uds_raw_aux_inst, mocker, uds_config, mock_count):
        send_mock = mocker.patch.object(uds_raw_aux_inst, "send_uds_config")
        uds_raw_aux_inst.uds_config_enable = uds_config

        uds_raw_aux_inst.write_data(parameter="test", value=b"\x01")
        assert send_mock.call_count == mock_count

    def test_Response_wrap(self, uds_raw_aux_inst, mock_uds_config, mocker):
        mock_uds_config.send.return_value = [0x7F, 0x03, 0x22]
        uds_raw_aux_inst.uds_config = mock_uds_config
        uds_raw_aux_inst.POSITIVE_RESPONSE_OFFSET = 0x40

        resp = uds_raw_aux_inst.send_uds_raw([0x10, 0x03])

        assert resp.is_negative is True
        assert resp.nrc == NegativeResponseCode.CONDITIONS_NOT_CORRECT

    def test_tester_present_sender(self, uds_raw_aux_inst, mocker):
        mocker.patch("time.sleep", return_value=None)
        send_mock = mocker.patch.object(uds_raw_aux_inst, "send_uds_raw")

        with uds_raw_aux_inst.tester_present_sender(1):
            sleep(3)

        send_mock.assert_called_with(
            UDSCommands.TesterPresent.TESTER_PRESENT_NO_RESPONSE,
            response_required=False,
        )

    def test_tester_present_sender_start_stop(self, mocker, uds_raw_aux_inst):
        send_mock = mocker.patch.object(uds_raw_aux_inst, "send_uds_raw")
        mocker.patch("time.sleep", return_value=None)

        uds_raw_aux_inst.start_tester_present_sender(1)
        uds_raw_aux_inst.stop_tester_present_sender()

        send_mock.assert_called_with(
            UDSCommands.TesterPresent.TESTER_PRESENT_NO_RESPONSE,
            response_required=False,
        )

    def test_tester_present_sender_stop_before_start(
        self, mocker, uds_raw_aux_inst, caplog
    ):
        send_mock = mocker.patch.object(uds_raw_aux_inst, "send_uds_raw")
        mocker.patch("time.sleep", return_value=None)

        uds_raw_aux_inst.stop_tester_present_sender()
        with caplog.at_level(logging.ERROR):
            assert (
                "Tester present sender should be started before it can be stopped"
                in caplog.text
            )

    def test_delete_aux_instance(self, mocker, uds_raw_aux_inst):
        mocker.patch.object(uds_raw_aux_inst, "send_uds_raw")
        mocker.patch("time.sleep", return_value=None)

        assert uds_raw_aux_inst.is_tester_present is None
        uds_raw_aux_inst.start_tester_present_sender(0.5)
        assert uds_raw_aux_inst.is_tester_present is not None
        assert uds_raw_aux_inst._delete_auxiliary_instance() is True
        assert uds_raw_aux_inst.is_tester_present is None
