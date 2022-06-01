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
import threading
from unittest import mock

import pytest

from pykiso.lib.auxiliaries.udsaux.common.odx_parser import OdxParser
from pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary import (
    UdsServerAuxiliary,
)

ODX_PARSER_RETURN = {
    0x123: {
        "name": "service",
        "subid": {"request": [1, 2, 3, 4], "response": [4, 3, 2, 1]},
    }
}


class TestUdsServerAuxiliary:
    uds_aux_instance_odx = None
    uds_aux_instance_raw = None

    @pytest.fixture(scope="function")
    def uds_server_aux_inst(self, mocker, ccpcan_inst, tmp_uds_config_ini):
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
        mocker.patch(
            "pykiso.lib.auxiliaries.udsaux.common.odx_parser.OdxParser.parse",
            return_value=ODX_PARSER_RETURN,
        )

        TestUdsServerAuxiliary.uds_aux_instance_odx = UdsServerAuxiliary(
            com=ccpcan_inst, config_ini_path=tmp_uds_config_ini, odx_file_path="odx"
        )
        return TestUdsServerAuxiliary.uds_aux_instance_odx

    def test_constructor_no_odx(
        self, uds_server_aux_inst, tmp_uds_config_ini, ccpcan_inst
    ):
        uds_server_inst = UdsServerAuxiliary(
            com=ccpcan_inst,
            config_ini_path=tmp_uds_config_ini,
            request_id=0x123,
            response_id=0x321,
        )

        assert uds_server_inst._ecu_config is None
        assert uds_server_inst._callbacks == {}
        assert uds_server_inst._callback_lock is not None
        assert uds_server_inst.req_id == 0x123
        assert uds_server_inst.res_id == 0x321

        uds_server_inst = UdsServerAuxiliary(
            com=ccpcan_inst, config_ini_path=tmp_uds_config_ini
        )

        assert uds_server_inst.req_id == 0xAB
        assert uds_server_inst.res_id == 0xAC

    def test_constructor_odx(
        self, mocker, uds_server_aux_inst, tmp_uds_config_ini, ccpcan_inst
    ):
        uds_server_inst = UdsServerAuxiliary(
            com=ccpcan_inst,
            config_ini_path=tmp_uds_config_ini,
            request_id=0x123,
            response_id=0x321,
            odx_file_path="dummy.odx",
        )

        assert uds_server_inst._ecu_config == ODX_PARSER_RETURN
        assert uds_server_inst._callbacks == {}
        assert uds_server_inst._callback_lock is not None

    @pytest.mark.parametrize(
        "data_len, expected_padded_len",
        [(7, 8), (9, 12), (20, 20), (21, 24), (42, 48), (62, 64)],
    )
    def test__pad_message(self, data_len, expected_padded_len):
        msg = [1] * data_len
        padded_msg = UdsServerAuxiliary._pad_message(msg)

        assert len(padded_msg) == expected_padded_len
        assert all(
            [
                el == UdsServerAuxiliary.CAN_FD_PADDING_PATTERN
                for el in padded_msg[data_len:]
            ]
        )

    @pytest.mark.parametrize("req_id, expected_req_id", [(None, 0xAB), (0x42, 0x42)])
    def test_transmit(self, mocker, uds_server_aux_inst, req_id, expected_req_id):
        data = [1, 2, 3, 4]
        mock_pad = mocker.patch.object(
            uds_server_aux_inst, "_pad_message", return_value=data
        )
        mock_channel = mocker.patch.object(uds_server_aux_inst, "channel")

        uds_server_aux_inst.transmit(data, req_id)

        mock_pad.assert_called_with(data)
        mock_channel._cc_send.assert_called_with(
            msg=data, remote_id=expected_req_id, raw=True
        )

    @pytest.mark.parametrize(
        "cc_receive_return, expected_received_data",
        [((None, 0xAC), None), ((b"DATA", 0xDC), None), ((b"DATA", 0xAC), b"DATA")],
    )
    def test_receive(
        self, mocker, uds_server_aux_inst, cc_receive_return, expected_received_data
    ):
        mock_channel = mocker.patch.object(uds_server_aux_inst, "channel")
        mock_channel._cc_receive.return_value = cc_receive_return

        received_data = uds_server_aux_inst.receive()

        uds_server_aux_inst.channel._cc_receive.assert_called_with(timeout=0, raw=True)
        assert received_data == expected_received_data

    def test_send_response(self, mocker, uds_server_aux_inst):
        uds_mock = mocker.patch(uds_server_aux_inst, "uds_config")
        uds_mock.tp.encode_isotp.return_value = "NOT NONE"
        mock_transmit = mocker.patch.object(uds_server_aux_inst, "transmit")

        uds_server_aux_inst.send_response(b"plop")

        uds_mock.tp.encode_isotp.assert_called_with(
            b"plop", use_external_snd_rcv_functions=True
        )
        mock_transmit.assert_called_with("NOT NONE", uds_server_aux_inst.req_id)

    @pytest.mark.parametrize(
        "stmin_in_ms, expected_stmin",
        [(0, 0), (1, 1), (127, 127), (0.1, 0xF1), (0.9, 0xF9), (0.10001, 0xF1)],
    )
    def test_encode_stmin(self, stmin_in_ms, expected_stmin):
        encoded_stmin = UdsServerAuxiliary.encode_stmin(stmin_in_ms)
        assert encoded_stmin == expected_stmin

    @pytest.mark.parametrize(
        "fs, bs, stmin, expected_flow_control",
        [
            (0, 0, 0, [0x30, 0x00, 0x00]),
            (1, 0x42, 0.1, [0x31, 0x42, 0xF1]),
            (0, 0, 0, [0x30, 0x00, 0x00]),
        ],
    )
    def test_send_flow_control(
        self, mocker, uds_server_aux_inst, fs, bs, stmin, expected_flow_control
    ):
        mock_transmit = mocker.patch.object(uds_server_aux_inst, "transmit")

        uds_server_aux_inst.send_flow_control(fs, bs, stmin)

        mock_transmit.assert_called_with(expected_flow_control)
