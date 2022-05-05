##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import pathlib
from pathlib import Path
from unittest import mock

import can as python_can
import pytest

from pykiso import Message
from pykiso.lib.connectors.cc_pcan_can import CCPCanCan, PCANBasic, can
from pykiso.message import (
    MessageAckType,
    MessageCommandType,
    MessageType,
    TlvKnownTags,
)

tlv_dict_to_send = {
    TlvKnownTags.TEST_REPORT: "OK",
    TlvKnownTags.FAILURE_REASON: b"\x12\x34\x56",
}

message_with_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
    tlv_dict=tlv_dict_to_send,
)

message_with_no_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
)


@pytest.fixture
def mock_can_bus(mocker):
    """fixture used to create mocker relative to can object from
    python-can package.
    """

    class MockCan:
        """Class used to stub can.interface.Bus method"""

        def __init__(self, **kwargs):
            """"""
            pass

        set_filters = mocker.stub(name="set_filters")
        shutdown = mocker.stub(name="shutdown")
        send = mocker.stub(name="send")
        recv = mocker.stub(name="recv")

    mocker.patch.object(can.interface, "Bus", new=MockCan)
    return can.interface


@pytest.fixture
def mock_PCANBasic(mocker):
    """fixture used to create mocker relative to PCANBasic object from
    PEAK's PCANBasic api.
    """

    class MockPCANBasic:
        """Class used to stub PCANBasic.PCANBasic() class"""

        def __init__(self, **kwargs):
            """"""
            pass

        def GetErrorText(self, error):
            return PCANBasic.PCAN_ERROR_OK, "ErrorText"

        SetValue = mocker.stub(name="SetValue")
        Uninitialize = mocker.stub(name="Uninitialize")

    mocker.patch.object(PCANBasic, "PCANBasic", new=MockPCANBasic)
    return PCANBasic


@pytest.mark.parametrize(
    "constructor_params, expected_config",
    [
        (
            {},
            {
                "interface": "pcan",
                "channel": "PCAN_USBBUS1",
                "state": "ACTIVE",
                "bitrate": 500000,
                "is_fd": True,
                "enable_brs": False,
                "f_clock_mhz": 80,
                "nom_brp": 2,
                "nom_tseg1": 63,
                "nom_tseg2": 16,
                "nom_sjw": 16,
                "data_brp": 4,
                "data_tseg1": 7,
                "data_tseg2": 2,
                "data_sjw": 2,
                "is_extended_id": False,
                "remote_id": None,
                "can_filters": None,
                "logging_activated": True,
                "bus_error_warning_filter": False,
            },
        ),
        (
            {
                "interface": "pcan",
                "channel": "PCAN_USBBUS1",
                "state": "ACTIVE",
                "bitrate": 500000,
                "is_fd": False,
                "enable_brs": True,
                "f_clock_mhz": 50,
                "nom_brp": 1,
                "nom_tseg1": 60,
                "nom_tseg2": 12,
                "nom_sjw": 4,
                "data_brp": 3,
                "data_tseg1": 7,
                "data_tseg2": 2,
                "data_sjw": 3,
                "is_extended_id": True,
                "remote_id": 0x10,
                "can_filters": [
                    {"can_id": 0x507, "can_mask": 0x7FF, "extended": False}
                ],
                "logging_activated": False,
                "bus_error_warning_filter": True,
            },
            {
                "interface": "pcan",
                "channel": "PCAN_USBBUS1",
                "state": "ACTIVE",
                "bitrate": 500000,
                "is_fd": False,
                "enable_brs": True,
                "f_clock_mhz": 50,
                "nom_brp": 1,
                "nom_tseg1": 60,
                "nom_tseg2": 12,
                "nom_sjw": 4,
                "data_brp": 3,
                "data_tseg1": 7,
                "data_tseg2": 2,
                "data_sjw": 3,
                "is_extended_id": True,
                "remote_id": 0x10,
                "can_filters": [
                    {"can_id": 0x507, "can_mask": 0x7FF, "extended": False}
                ],
                "logging_activated": False,
                "bus_error_warning_filter": True,
            },
        ),
    ],
)
def test_constructor(constructor_params, expected_config, caplog):

    param = constructor_params.values()
    with caplog.at_level(logging.WARNING):
        can_inst = CCPCanCan(*param)
    log = logging.getLogger("can.pcan")
    log.info("Bus error: an error counter")
    assert can_inst.interface == expected_config["interface"]
    assert can_inst.channel == expected_config["channel"]
    assert can_inst.bitrate == expected_config["bitrate"]
    assert can_inst.remote_id == expected_config["remote_id"]
    assert can_inst.f_clock_mhz == expected_config["f_clock_mhz"]
    assert can_inst.is_fd == expected_config["is_fd"]
    assert can_inst.enable_brs == expected_config["enable_brs"]
    assert can_inst.nom_brp == expected_config["nom_brp"]
    assert can_inst.nom_tseg1 == expected_config["nom_tseg1"]
    assert can_inst.nom_tseg2 == expected_config["nom_tseg2"]
    assert can_inst.nom_sjw == expected_config["nom_sjw"]
    assert can_inst.data_brp == expected_config["data_brp"]
    assert can_inst.data_tseg1 == expected_config["data_tseg1"]
    assert can_inst.data_tseg2 == expected_config["data_tseg2"]
    assert can_inst.data_sjw == expected_config["data_sjw"]
    assert can_inst.bus == None
    assert can_inst.is_extended_id == expected_config["is_extended_id"]
    assert can_inst.can_filters == expected_config["can_filters"]
    assert can_inst.logging_activated == expected_config["logging_activated"]
    assert can_inst.timeout == 1e-6

    if not can_inst.is_fd and can_inst.enable_brs:
        assert "Bitrate switch will have no effect" in caplog.text

    if expected_config["bus_error_warning_filter"]:
        assert "Bus error: an error counter" not in caplog.text
    else:
        assert "Bus error: an error counter" in caplog.text


@pytest.mark.parametrize(
    "logging_requested",
    [
        (True),
        (False),
    ],
)
def test_cc_open(
    logging_requested,
    mock_can_bus,
    mock_PCANBasic,
):
    can_inst = CCPCanCan(logging_activated=logging_requested)
    with mock.patch.object(
        can_inst, "_pcan_configure_trace"
    ) as mock_pcan_configure_trace:
        can_inst._cc_open()

    assert isinstance(can_inst.bus, mock_can_bus.Bus) == True
    assert can_inst.bus != None
    if logging_requested:
        assert type(can_inst.raw_pcan_interface) is type(PCANBasic.PCANBasic())
    else:
        assert can_inst.raw_pcan_interface is None
    assert mock_pcan_configure_trace.called == logging_requested


@pytest.mark.parametrize(
    "side_effects, os_makedirs_error, logging_info_count, logging_error_count, logging_path",
    [
        ([None, None, None], None, 2, 0, None),
        ([None, None, None], None, 4, 0, (pathlib.Path.cwd() / "test/path")),
        (
            [RuntimeError("Test Exception 1"), None, None],
            None,
            1,
            1,
            (pathlib.Path.cwd() / "test/path"),
        ),
        (
            [None, RuntimeError("Test Exception 2"), None],
            None,
            2,
            1,
            (pathlib.Path.cwd() / "test/path"),
        ),
        (
            [None, None, RuntimeError("Test Exception 3")],
            None,
            3,
            1,
            (pathlib.Path.cwd() / "test/path"),
        ),
        (
            [None, None, None],
            OSError("Test Exception 4"),
            0,
            2,
            (pathlib.Path.cwd() / "test/path"),
        ),
    ],
)
def test_pcan_configure_trace(
    caplog,
    side_effects,
    os_makedirs_error,
    logging_info_count,
    logging_error_count,
    logging_path,
):
    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")
    can_inst = CCPCanCan()
    caplog.clear()
    can_inst.logging_path = logging_path
    with mock.patch.object(pathlib.Path, "mkdir", side_effect=os_makedirs_error):
        with mock.patch.object(can_inst, "_pcan_set_value", side_effect=side_effects):
            can_inst._pcan_configure_trace()
            info_logs = [
                record for record in caplog.records if record.levelname == "INFO"
            ]
            error_logs = [
                record for record in caplog.records if record.levelname == "ERROR"
            ]
            assert len(info_logs) == logging_info_count
            assert len(error_logs) == logging_error_count


@pytest.mark.parametrize(
    "return_value, side_effect, RuntimeError_raised",
    [
        (PCANBasic.PCAN_ERROR_OK, None, False),
        (PCANBasic.PCAN_ERROR_UNKNOWN, None, True),
        (PCANBasic.PCAN_ERROR_OK, RuntimeError("Test Exception 1"), True),
    ],
)
def test_pcan_set_value(
    return_value,
    side_effect,
    RuntimeError_raised,
    mock_PCANBasic,
):
    can_inst = CCPCanCan()
    can_inst.raw_pcan_interface = PCANBasic.PCANBasic()
    with mock.patch.object(
        can_inst.raw_pcan_interface,
        "SetValue",
        return_value=return_value,
        side_effect=side_effect,
    ):
        if RuntimeError_raised:
            with pytest.raises(RuntimeError):
                can_inst._pcan_set_value(
                    PCANBasic.PCAN_USBBUS1,
                    PCANBasic.PCAN_TRACE_CONFIGURE,
                    PCANBasic.TRACE_FILE_OVERWRITE,
                )
        else:
            can_inst._pcan_set_value(
                PCANBasic.PCAN_USBBUS1,
                PCANBasic.PCAN_TRACE_CONFIGURE,
                PCANBasic.TRACE_FILE_OVERWRITE,
            )


def test_cc_close_logging_deactivated(caplog, mock_can_bus, mock_PCANBasic):

    with caplog.at_level(logging.ERROR, logger="pykiso.lib.connectors.cc_pcan_can.log"):
        with CCPCanCan(logging_activated=False) as can_inst:
            pass
        mock_can_bus.Bus.shutdown.assert_called_once()
        assert can_inst.bus == None
        assert mock_PCANBasic.PCANBasic.Uninitialize.called == False
        assert not caplog.records


def test_cc_close(
    caplog,
    mock_can_bus,
    mock_PCANBasic,
):
    mock_PCANBasic.PCANBasic.SetValue.return_value = PCANBasic.PCAN_ERROR_OK
    mock_PCANBasic.PCANBasic.Uninitialize.side_effect = [PCANBasic.PCAN_ERROR_OK]

    with caplog.at_level(logging.ERROR, logger="pykiso.lib.connectors.cc_pcan_can.log"):
        with CCPCanCan() as can_inst:
            pass

        mock_can_bus.Bus.shutdown.assert_called_once()
        assert can_inst.bus == None
        assert mock_PCANBasic.PCANBasic.Uninitialize.called == True
        assert not caplog.records


def test_cc_close_with_error(
    caplog,
    mock_can_bus,
    mock_PCANBasic,
):
    mock_PCANBasic.PCANBasic.SetValue.return_value = PCANBasic.PCAN_ERROR_OK
    mock_PCANBasic.PCANBasic.Uninitialize.side_effect = [PCANBasic.PCAN_ERROR_UNKNOWN]

    with caplog.at_level(logging.ERROR, logger="pykiso.lib.connectors.cc_pcan_can.log"):
        with CCPCanCan() as can_inst:
            pass

        mock_can_bus.Bus.shutdown.assert_called_once()
        assert can_inst.bus == None
        assert mock_PCANBasic.PCANBasic.Uninitialize.called == True
        assert "Exception" not in caplog.text
        assert len(caplog.records) == 1


def test_cc_close_with_exception(
    caplog,
    mock_can_bus,
    mock_PCANBasic,
):
    mock_PCANBasic.PCANBasic.SetValue.return_value = PCANBasic.PCAN_ERROR_OK
    mock_PCANBasic.PCANBasic.Uninitialize.side_effect = [Exception("Test Exception")]

    with caplog.at_level(logging.ERROR, logger="pykiso.lib.connectors.cc_pcan_can.log"):
        with CCPCanCan() as can_inst:
            pass

        mock_can_bus.Bus.shutdown.assert_called_once()
        assert can_inst.bus == None
        assert mock_PCANBasic.PCANBasic.Uninitialize.called == True
        assert "Exception" in caplog.text
        assert len(caplog.records) == 1


@pytest.mark.parametrize(
    "parameters",
    [
        (b"\x10\x36", 0x0A, True),
        (b"\x10\x36", None, True),
        (b"\x10\x36", 10, True),
        (b"", 10, True),
        (message_with_tlv, 0x0A, False),
        (message_with_no_tlv, 0x0A, False),
        (message_with_no_tlv,),
        (message_with_no_tlv, 36),
    ],
)
def test_cc_send(mock_can_bus, parameters, mock_PCANBasic):

    with CCPCanCan(remote_id=0x0A) as can:
        can._cc_send(*parameters)

    mock_can_bus.Bus.send.assert_called_once()
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_data, can_id, cc_receive_param,expected_type",
    [
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", 0x500, (10, False), Message),
        (
            b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
            0x207,
            (None, None),
            Message,
        ),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, (10, True), bytearray),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, (0, True), bytearray),
    ],
)
def test_can_recv(
    mocker,
    mock_can_bus,
    raw_data,
    can_id,
    cc_receive_param,
    expected_type,
    mock_PCANBasic,
):
    mock_bus_recv = mocker.patch(
        "can.interface.Bus.recv",
        return_value=python_can.Message(data=raw_data, arbitration_id=can_id),
    )
    with CCPCanCan() as can:
        msg_received, id_received = can._cc_receive(*cc_receive_param)

    assert isinstance(msg_received, expected_type) == True
    assert id_received == can_id
    mock_can_bus.Bus.recv.assert_called_once_with(timeout=cc_receive_param[0] or 1e-6)
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_state",
    [
        True,
        False,
    ],
)
def test_can_recv_invalid(mocker, mock_can_bus, raw_state, mock_PCANBasic):

    mocker.patch("can.interface.Bus.recv", return_value=None)

    with CCPCanCan() as can:
        msg_received, id_received = can._cc_receive(timeout=0.0001, raw=raw_state)

    assert msg_received == None
    assert id_received == None


def test_can_recv_exception(caplog, mocker, mock_can_bus, mock_PCANBasic):

    mocker.patch("can.interface.Bus.recv", side_effect=Exception())

    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")

    with CCPCanCan() as can:
        msg_received, id_received = can._cc_receive(timeout=0.0001)

    assert msg_received == None
    assert id_received == None
    assert "Exception" in caplog.text


def test_can_recv_can_error_exception(caplog, mocker, mock_can_bus, mock_PCANBasic):

    mocker.patch(
        "can.interface.Bus.recv", side_effect=python_can.CanError("Invalid Message")
    )

    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")

    with caplog.at_level(logging.DEBUG):

        with CCPCanCan() as can:
            msg_received, id_received = can._cc_receive(timeout=0.0001)

    assert msg_received == None
    assert id_received == None
    assert "encountered can error: Invalid Message" in caplog.text
