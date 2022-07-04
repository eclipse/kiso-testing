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
from unittest.mock import MagicMock, call

import pytest

from pykiso.lib.auxiliaries.udsaux.common.uds_callback import (
    UdsCallback,
    UdsDownloadCallback,
)


@pytest.fixture()
def aux_mock(mocker):
    class MockAux:
        send_response = mocker.stub(name="send_response")
        send_flow_control = mocker.stub(name="send_flow_control")
        format_data = mocker.stub(name="format_data")
        stop_event = MagicMock(name="stop_event")
        receive = MagicMock(name="receive")

    return MockAux()


class TestUdsCallback:
    @pytest.mark.parametrize(
        "req, resp, data, data_len, expected_resp",
        [
            (0x0102, 0x0201, None, None, [0x02, 0x01]),
            ([0x01, 0x02], [0x02, 0x01], None, None, [0x02, 0x01]),
            (0x0102, None, 0x0304, 6, [0x41, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00]),
            (
                0x0102,
                None,
                b"\x03\x04",
                6,
                [0x41, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00],
            ),
        ],
    )
    def test_post_init(self, req, resp, data, data_len, expected_resp):
        callback = UdsCallback(req, resp, data, data_len)

        assert callback.request == [0x01, 0x02]
        assert callback.response == expected_resp
        assert callback.call_count == 0
        assert callback.callback is None

    @pytest.mark.parametrize(
        "custom_callback, custom_callback_calls, send_response_calls",
        [
            (None, 0, 1),
            (MagicMock(name="custom_callback"), 1, 0),
        ],
    )
    def test_call(
        self, aux_mock, custom_callback, custom_callback_calls, send_response_calls
    ):
        request = [0x01, 0x02]
        callback_inst = UdsCallback(request, [0x02, 0x01])
        callback_inst.callback = custom_callback

        callback_ret = callback_inst(request, aux_mock)

        assert callback_ret is None
        assert aux_mock.send_response.call_count == send_response_calls

        if custom_callback_calls:
            assert callback_inst.callback.call_count == custom_callback_calls
            callback_inst.callback.assert_called_with(request, aux_mock)
        elif send_response_calls:
            aux_mock.send_response.assert_called_with(callback_inst.response)


class TestUdsDownloadCallback:
    def test_download_callback_init(self):
        callback_inst = UdsDownloadCallback(stmin=12)

        assert UdsDownloadCallback.MAX_TRANSFER_SIZE == 0xFFFF

        assert isinstance(callback_inst, UdsCallback)
        assert callback_inst.call_count == 0
        assert callback_inst.request == [0x34]
        assert callback_inst.callback == callback_inst.handle_data_download
        assert callback_inst.transfer_successful is False
        assert callback_inst.transferred_data_size == 0

    @pytest.mark.parametrize(
        "download_req, expected_transfer_size",
        [
            ([0x34, 0x00, 0x23, 0x01, 0x02, 0x03, 0xFF, 0xFF, 0x0F], 0xFF_FE),
            ([0x34, 0x00, 0x12, 0x01, 0xFF, 0xFF], 0xFE),
        ],
    )
    def test_get_transfer_size(self, download_req, expected_transfer_size):
        transfer_size = UdsDownloadCallback.get_transfer_size(download_req)
        assert transfer_size == expected_transfer_size

    @pytest.mark.parametrize(
        "first_frame, expected_data_len, expected_uds_start_idx",
        [
            ([0x10, 0x00, 0x01, 0x02, 0x03, 0x04], 0x01020304, 6),
            ([0x11, 0x01, 0x02, 0x03, 0x04, 0x05], 0x101, 2),
        ],
    )
    def test_get_first_frame_data_len(
        self, first_frame, expected_data_len, expected_uds_start_idx
    ):
        data_len, uds_start_idx = UdsDownloadCallback.get_first_frame_data_length(
            first_frame
        )
        assert data_len == expected_data_len
        assert uds_start_idx == expected_uds_start_idx

    @pytest.mark.parametrize(
        "max_transfer_size, expected_response",
        [
            (None, [0x74, 0x20, 0xFF, 0xFF]),
            (0xFEFDFC, [0x74, 0x30, 0xFE, 0xFD, 0xFC]),
        ],
    )
    def test_make_request_download_response(self, max_transfer_size, expected_response):
        callback_inst = UdsDownloadCallback()
        response = callback_inst.make_request_download_response(max_transfer_size)
        assert response == expected_response

    def test_handle_data_download(self, caplog, mocker, aux_mock):
        UdsDownloadCallback.TRANSFER_TIMEOUT = 0.1
        req = [0x34, 0x00]

        callback_inst = UdsDownloadCallback()

        mock_req_download_resp = mocker.patch.object(
            callback_inst, "make_request_download_response", return_value=b"gogogo"
        )
        mock_get_transfer_size = mocker.patch.object(
            callback_inst, "get_transfer_size", return_value=2
        )
        # return 3 bytes of size to receive
        mock_get_first_frame_data_length = mocker.patch.object(
            callback_inst, "get_first_frame_data_length", side_effect=[(3, 6), (3, 6)]
        )
        aux_mock.stop_event.is_set.return_value = False
        initial_transfer_data = [0x00] * 6 + [0x36, 0x01, 0x02]
        aux_mock.receive.side_effect = (
            None,  # no initial transfer_data
            initial_transfer_data,  # initial transfer_data
            None,  # no block data
            [0x29, 0x00],  # invalid block data -> transfer_data += 1
            [0x22, 0x00],  # valid block data -> transfer_data += 1
        )

        assert callback_inst.transfer_successful is False

        callback_inst.handle_data_download(req, aux_mock)

        mock_req_download_resp.assert_called_once()
        mock_get_transfer_size.assert_called_with(req)
        mock_get_first_frame_data_length.assert_called_with(initial_transfer_data)

        aux_mock.send_response.assert_has_calls([call(b"gogogo"), call([0x76, 0x01])])

        assert "Consecutive frame missed" in caplog.text

        assert callback_inst.transfer_successful is True
        assert callback_inst.transferred_data_size == 3
