##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import datetime
import importlib
import logging
import os
import pathlib
import sys
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import can as python_can
import pytest

from pykiso import Message
from pykiso.lib.connectors.cc_pcan_can import cc_pcan_can
from pykiso.lib.connectors.cc_pcan_can.cc_pcan_can import CCPCanCan, PCANBasic, can
from pykiso.lib.connectors.cc_pcan_can.trc_handler import TRCReaderCanFD
from pykiso.message import MessageAckType, MessageCommandType, MessageType, TlvKnownTags

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
trc_data_start_1 = """;$FILEVERSION=2.0
;$STARTTIME=55555.0000000000\n"""

trc_data_start_2 = """;$FILEVERSION=2.0
;$STARTTIME=55555.0000001158\n"""

trc_data_start_3 = """;$FILEVERSION=2.0
;$STARTTIME=55555.0000011575\n"""

trc_data_start_4 = """;$FILEVERSION=1.1
;$STARTTIME=55555.0000000000\n"""

trc_data_start_5 = """;$FILEVERSION=1.1
;$STARTTIME=55555.0000001158\n"""

trc_data_start_6 = """;$FILEVERSION=1.1
;$STARTTIME=55555.0000011575\n"""


trc_data_end = """;$COLUMNS=N,O,T,I,d,L,D
;
;   /usr/src/python-lbach/test/test_pcan_trc.trc
;   Start time: 14/12/2022 15:44:50.000.0
;   Generated by PCAN-Basic API v4.6.1.32
;-------------------------------------------------------------------------------
;   Connection                                Bit rate
;   PCAN_USBBUS1 (/dev/pcan32)           f_clock=0000,nom_brp=0,nom_tseg1=00,nom_tseg2=00,nom_sjw=00,data_brp=0,data_tseg1=0,data_tseg2=0,data_sjw=0,
;                                        Nominal: 000 kBit/s (0x000), Data: 0 MBit/s (00 MHz)
;-------------------------------------------------------------------------------
; Glossary:
;   Direction of Message:
;     Rx: The frame was received
;     Tx: The frame was transmitted
;
;   Type of message:
;     DT: CAN or J1939 data frame
;     FD: CAN FD data frame
;     FB: CAN FD data frame with BRS bit set (Bit Rate Switch)
;     FE: CAN FD data frame with ESI bit set (Error State Indicator)
;     BI: CAN FD data frame with both BRS and ESI bits set
;     RR: Remote Request Frame
;     ST: Hardware Status change
;     ER: Error Frame
;     EV: Event. User-defined text, begins directly after 2-digit type indicator
;-------------------------------------------------------------------------------
;   Message   Time    Type ID     Rx/Tx
;   Number    Offset  |    [hex]  |  Data Length Code
;   |         [ms]    |    |      |  |  Data [hex]
;   |         |       |    |      |  |  |
;---+-- ------+------ +- --+----- +- +- +- -- -- -- -- -- -- --
      1         1.000 ST          Rx    00 00 00 00
      2         2.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      3         3.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      4         4.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00\n"""

trc_merge_data = """;$FILEVERSION=2.0
;$STARTTIME=55555.0000000000
;$COLUMNS=N,O,T,I,d,L,D
;
;   /usr/src/python-lbach/test/test_pcan_trc.trc
;   Start time: 14/12/2022 15:44:50.000.0
;   Generated by PCAN-Basic API v4.6.1.32
;-------------------------------------------------------------------------------
;   Connection                                Bit rate
;   PCAN_USBBUS1 (/dev/pcan32)           f_clock=0000,nom_brp=0,nom_tseg1=00,nom_tseg2=00,nom_sjw=00,data_brp=0,data_tseg1=0,data_tseg2=0,data_sjw=0,
;                                        Nominal: 000 kBit/s (0x000), Data: 0 MBit/s (00 MHz)
;-------------------------------------------------------------------------------
; Glossary:
;   Direction of Message:
;     Rx: The frame was received
;     Tx: The frame was transmitted
;
;   Type of message:
;     DT: CAN or J1939 data frame
;     FD: CAN FD data frame
;     FB: CAN FD data frame with BRS bit set (Bit Rate Switch)
;     FE: CAN FD data frame with ESI bit set (Error State Indicator)
;     BI: CAN FD data frame with both BRS and ESI bits set
;     RR: Remote Request Frame
;     ST: Hardware Status change
;     ER: Error Frame
;     EV: Event. User-defined text, begins directly after 2-digit type indicator
;-------------------------------------------------------------------------------
;   Message   Time    Type ID     Rx/Tx
;   Number    Offset  |    [hex]  |  Data Length Code
;   |         [ms]    |    |      |  |  Data [hex]
;   |         |       |    |      |  |  |
;---+-- ------+------ +- --+----- +- +- +- -- -- -- -- -- -- --
      1         1.000 ST          Rx    00 00 00 00
      2         2.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      3         3.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      4         4.000 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      5        21.010 ST          Rx    00 00 00 00
      6        22.010 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      7        23.010 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      8        24.010 FB     0200 Rx 8  00 00 00 00 00 00 00 00
      9       201.016 ST          Rx    00 00 00 00
     10       202.016 FB     0200 Rx 8  00 00 00 00 00 00 00 00
     11       203.016 FB     0200 Rx 8  00 00 00 00 00 00 00 00
     12       204.016 FB     0200 Rx 8  00 00 00 00 00 00 00 00\n"""


@pytest.fixture
def mock_trc_reader(mocker):
    class MockTrcReader:
        def __init__(self, **kwargs):
            pass

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")

    return MockTrcReader()


@pytest.fixture
def trc_files(tmp_path):
    """
    create fake trc files at a temporary directory
    """
    traces = [
        trc_data_start_1 + trc_data_end,
        trc_data_start_2 + trc_data_end,
        trc_data_start_3 + trc_data_end,
    ]
    trc_folder = Path(tmp_path / "traces")
    trc_folder.mkdir(parents=True, exist_ok=True)
    file_paths = [
        trc_folder / "trc_1.trc",
        trc_folder / "trc_2.trc",
        trc_folder / "trc_3.trc",
    ]
    for idx, file in enumerate(file_paths):
        with open(file, "w+") as f:
            f.write(traces[idx])
            # Sleep to avoid failure on integration tests
        os.utime(file, (1602179630 + idx * 2, 1602179630 + idx * 2))
    return file_paths


@pytest.fixture
def trc_files_different_directory(tmp_path):
    """
    create fake trc files at two temporary directories
    """
    traces = [
        trc_data_start_1 + trc_data_end,
        trc_data_start_2 + trc_data_end,
        trc_data_start_3 + trc_data_end,
    ]
    trc_folder = Path(tmp_path / "traces")
    trc_folder.mkdir(parents=True, exist_ok=True)
    trc_second_folder = Path(tmp_path / "traces_second_repo")
    trc_second_folder.mkdir(parents=True, exist_ok=True)
    file_paths = [
        trc_folder / "trc_1.trc",
        trc_folder / "trc_2.trc",
        trc_second_folder / "trc_3.trc",
    ]
    for idx, file in enumerate(file_paths):
        with open(file, "w+") as f:
            f.write(traces[idx])
            # Sleep to avoid failure on integration tests
        os.utime(file, (1602179630 + idx * 2, 1602179630 + idx * 2))
    return file_paths


@pytest.fixture
def trc_files_v1_1(tmp_path):
    """
    create fake trc files at a temporary directory
    """
    traces = [
        trc_data_start_4 + trc_data_end,
        trc_data_start_5 + trc_data_end,
        trc_data_start_6 + trc_data_end,
    ]
    trc_folder = Path(tmp_path / "traces")
    trc_folder.mkdir(parents=True, exist_ok=True)
    file_paths = [
        trc_folder / "trc_4.trc",
        trc_folder / "trc_5.trc",
        trc_folder / "trc_6.trc",
    ]
    for idx, file in enumerate(file_paths):
        with open(file, "w+") as f:
            f.write(traces[idx])
            # Sleep to avoid failure on integration tests
        os.utime(file, (1602179630 + idx * 2, 1602179630 + idx * 2))
    return file_paths


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

        def SetValue(self, Channel, Parameter, Buffer):
            pass

        Uninitialize = mocker.stub(name="Uninitialize")

    mocker.patch.object(MockPCANBasic, "SetValue", return_value=PCANBasic.PCAN_ERROR_OK)
    mocker.patch.object(PCANBasic, "PCANBasic", new=MockPCANBasic)
    return PCANBasic


def test_import():
    with pytest.raises(ImportError):
        sys.modules["can"] = None
        importlib.reload(cc_pcan_can)
    sys.modules["can"] = can
    importlib.reload(cc_pcan_can)


def test_import_uptime():
    sys.modules["uptime"] = None
    importlib.reload(cc_pcan_can)
    assert cc_pcan_can.boottime_epoch == 0


@pytest.mark.parametrize(
    "constructor_params, expected_config",
    [
        (
            {},
            {
                "interface": "pcan",
                "channel": "PCAN_USBBUS1",
                "state": "ACTIVE",
                "trace_path": "result.trc",
                "trace_size": 10,
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
                "trace_path": "result.trc",
                "trace_size": 1000,
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
                "can_filters": [{"can_id": 0x507, "can_mask": 0x7FF, "extended": False}],
                "logging_activated": False,
                "bus_error_warning_filter": True,
            },
            {
                "interface": "pcan",
                "channel": "PCAN_USBBUS1",
                "state": "ACTIVE",
                "trace_path": "result.trc",
                "trace_size": 10,
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
                "can_filters": [{"can_id": 0x507, "can_mask": 0x7FF, "extended": False}],
                "logging_activated": False,
                "bus_error_warning_filter": True,
            },
        ),
    ],
)
def test_constructor(constructor_params, expected_config, caplog, mocker):

    mocker.patch.object(pathlib.Path, "is_file", return_value=False)

    param = constructor_params.values()
    log = logging.getLogger("can.pcan")

    with caplog.at_level(logging.INTERNAL_WARNING):
        can_inst = CCPCanCan(*param)
    log.warning("Bus error: an error counter")
    can_inst.trace_path = ""
    assert can_inst.interface == expected_config["interface"]
    assert can_inst.channel == expected_config["channel"]
    assert can_inst.bitrate == expected_config["bitrate"]
    assert can_inst.trace_size == expected_config["trace_size"]
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


def test_initialize_trace(mocker, mock_can_bus, mock_PCANBasic):

    mocker.patch.object(CCPCanCan, "_merge_trc")

    can_inst = CCPCanCan(trace_path="result.trc")
    assert can_inst.trace_path == Path(".")
    assert can_inst.trace_name == "result.trc"

    can_inst = CCPCanCan(trace_path="folder/")
    assert can_inst.trace_path == Path("folder/")
    assert can_inst.trace_name is None

    can_inst = CCPCanCan()
    assert can_inst.trace_path == Path(".")
    assert can_inst.trace_name is None

    with pytest.raises(ValueError):
        can_inst = CCPCanCan(trace_path="result_file.txt")


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
    with mock.patch.object(can_inst, "_pcan_configure_trace") as mock_pcan_configure_trace:
        can_inst._cc_open()

    assert isinstance(can_inst.bus, mock_can_bus.Bus) == True
    assert can_inst.bus != None
    if logging_requested:
        assert type(can_inst.raw_pcan_interface) is type(PCANBasic.PCANBasic())
    else:
        assert can_inst.raw_pcan_interface is None
    assert mock_pcan_configure_trace.called == logging_requested


@mock.patch("sys.platform", "darwin")
def test_macos_instantiation(mock_can_bus, mock_PCANBasic, mocker, caplog):
    # Instantiation to test
    connector = CCPCanCan(logging_activated=True)
    # Run the action to test
    with caplog.at_level(logging.INTERNAL_DEBUG):
        connector._cc_open()
    # Validation of the warning popped
    assert "TRACE_FILE_SEGMENTED deactivated for macos!" in [record.getMessage() for record in caplog.records]


@pytest.mark.parametrize(
    "side_effects, os_makedirs_error, logging_info_count, logging_error_count, logging_path, trace_option",
    [
        (
            [None, None, None, None],
            None,
            4,
            0,
            None,
            True,
        ),
        (
            [None, None, None, None, None],
            None,
            6,
            0,
            (pathlib.Path.cwd() / "test/path"),
            False,
        ),
        (
            [RuntimeError("Test Exception 1"), None, None, None],
            None,
            1,
            1,
            (pathlib.Path.cwd() / "test/path"),
            True,
        ),
        (
            [None, RuntimeError("Test Exception 2"), None, None],
            None,
            3,
            1,
            (pathlib.Path.cwd() / "test/path"),
            True,
        ),
        (
            [None, None, RuntimeError("Test Exception 3"), None],
            None,
            4,
            1,
            (pathlib.Path.cwd() / "test/path"),
            True,
        ),
        (
            [None, None, None, None],
            OSError("Test Exception 4"),
            0,
            2,
            (pathlib.Path.cwd() / "test/path"),
            True,
        ),
    ],
)
@mock.patch("sys.platform", "linux")
def test_pcan_configure_trace(
    caplog,
    mocker,
    side_effects,
    os_makedirs_error,
    logging_info_count,
    logging_error_count,
    logging_path,
    trace_option,
):
    mocker.patch.object(CCPCanCan, "_merge_trc")
    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")
    can_inst = CCPCanCan()
    caplog.clear()
    can_inst.trace_path = logging_path
    can_inst.trace_size = 11
    can_inst.segmented = trace_option
    with mock.patch.object(pathlib.Path, "mkdir", side_effect=os_makedirs_error):
        with mock.patch.object(can_inst, "_pcan_set_value", side_effect=side_effects):
            can_inst._pcan_configure_trace()
            info_logs = [record for record in caplog.records if record.levelname == "INTERNAL_INFO"]
            error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
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
        assert can_inst.bus is None
        mock_PCANBasic.PCANBasic.Uninitialize.assert_not_called()
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
        mock_PCANBasic.PCANBasic.Uninitialize.assert_called()
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
        assert can_inst.bus is None
        mock_PCANBasic.PCANBasic.Uninitialize.assert_called()
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
    "parameters,raw",
    [
        ({"msg": b"\x10\x36", "remote_id": 0x0A}, True),
        ({"msg": b"\x10\x36", "remote_id": None}, True),
        ({"msg": b"\x10\x36", "remote_id": 10}, True),
        ({"msg": b"", "remote_id": 10}, True),
        ({"msg": message_with_tlv, "remote_id": 0x0A}, False),
        ({"msg": message_with_no_tlv, "remote_id": 0x0A}, False),
        ({"msg": message_with_no_tlv}, False),
        ({"msg": message_with_no_tlv, "remote_id": 36}, False),
    ],
)
def test_cc_send(mock_can_bus, parameters, raw, mock_PCANBasic):
    if not raw:
        parameters["msg"] = parameters.get("msg").serialize()
    with CCPCanCan(remote_id=0x0A) as can:
        can._cc_send(**parameters)

    mock_can_bus.Bus.send.assert_called_once()
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_data, can_id, timeout, raw,expected_type, timestamp",
    [
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", 0x500, 10, False, Message, 1),
        (
            b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
            0x207,
            None,
            None,
            Message,
            2,
        ),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 10, True, bytearray, 3),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 0, True, bytearray, 4),
    ],
)
def test_can_recv(
    mock_can_bus,
    raw_data,
    can_id,
    timeout,
    timestamp,
    raw,
    expected_type,
    mock_PCANBasic,
):
    mock_can_bus.Bus.recv.return_value = python_can.Message(data=raw_data, arbitration_id=can_id, timestamp=timestamp)

    with CCPCanCan() as can:
        response = can._cc_receive(timeout)

    msg_received = response.get("msg")
    if not raw:
        msg_received = Message.parse_packet(msg_received)

    assert response.get("timestamp") == timestamp
    assert isinstance(msg_received, expected_type)
    assert response.get("remote_id") == can_id
    mock_can_bus.Bus.recv.assert_called_once_with(timeout=timeout or 1e-6)
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_state",
    [
        True,
        False,
    ],
)
def test_can_recv_invalid(mocker, mock_can_bus, raw_state, mock_PCANBasic):

    mocker.patch("can.interface.Bus.recv", return_value={"msg": None})

    with CCPCanCan() as can:
        response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None


def test_can_recv_exception(caplog, mocker, mock_can_bus, mock_PCANBasic):

    mocker.patch("can.interface.Bus.recv", side_effect=Exception())

    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")

    with CCPCanCan() as can:
        response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None
    assert "Exception" in caplog.text


def test_can_recv_can_error_exception(caplog, mocker, mock_can_bus, mock_PCANBasic):

    mocker.patch("can.interface.Bus.recv", side_effect=python_can.CanError("Invalid Message"))

    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")

    with caplog.at_level(logging.INTERNAL_DEBUG):

        with CCPCanCan() as can:
            response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None
    assert "encountered CAN error while receiving message: Invalid Message" in caplog.text


def test_extract_header(trc_files):
    header_data = """;$FILEVERSION=2.0
;$STARTTIME=55555.0000000000
;$COLUMNS=N,O,T,I,d,L,D
;
;   /usr/src/python-lbach/test/test_pcan_trc.trc
;   Start time: 14/12/2022 15:44:50.000.0
;   Generated by PCAN-Basic API v4.6.1.32
;-------------------------------------------------------------------------------
;   Connection                                Bit rate
;   PCAN_USBBUS1 (/dev/pcan32)           f_clock=0000,nom_brp=0,nom_tseg1=00,nom_tseg2=00,nom_sjw=00,data_brp=0,data_tseg1=0,data_tseg2=0,data_sjw=0,
;                                        Nominal: 000 kBit/s (0x000), Data: 0 MBit/s (00 MHz)
;-------------------------------------------------------------------------------
; Glossary:
;   Direction of Message:
;     Rx: The frame was received
;     Tx: The frame was transmitted
;
;   Type of message:
;     DT: CAN or J1939 data frame
;     FD: CAN FD data frame
;     FB: CAN FD data frame with BRS bit set (Bit Rate Switch)
;     FE: CAN FD data frame with ESI bit set (Error State Indicator)
;     BI: CAN FD data frame with both BRS and ESI bits set
;     RR: Remote Request Frame
;     ST: Hardware Status change
;     ER: Error Frame
;     EV: Event. User-defined text, begins directly after 2-digit type indicator
;-------------------------------------------------------------------------------
;   Message   Time    Type ID     Rx/Tx
;   Number    Offset  |    [hex]  |  Data Length Code
;   |         [ms]    |    |      |  |  Data [hex]
;   |         |       |    |      |  |  |
;---+-- ------+------ +- --+----- +- +- +- -- -- -- -- -- -- --
"""

    result = CCPCanCan._extract_header(trc_files[0])
    assert result == header_data


def test_merge_trc(trc_files, mock_can_bus, mock_PCANBasic):

    path = trc_files[0].parent
    result_path = trc_files[0].parent / "trc_1.trc"
    cc_pcan = CCPCanCan(trace_path=path)
    cc_pcan._trc_file_names[str(path)] = []
    for file in trc_files:
        cc_pcan._trc_file_names[str(file.parent)].append(None)

    cc_pcan._merge_trc()

    with open(result_path, "r") as trc:
        result = trc.read()

    assert trc_merge_data == result


def test_merge_trc_with_file_name(trc_files, mock_can_bus, mock_PCANBasic):
    trc_files[0] = trc_files[0].parent / "result_file.trc"

    cc_pcan = CCPCanCan(trace_path=trc_files[0].parent)
    cc_pcan._trc_file_names[trc_files[0].parent] = []
    for file in trc_files:
        cc_pcan._trc_file_names[file.parent].append(file.name)
    result_path = trc_files[0]
    cc_pcan._merge_trc()

    with open(result_path, "r") as trc:
        result = trc.read()

    assert trc_merge_data == result


def test_merge_trc_with_old_file_version(trc_files_v1_1, mock_can_bus, mock_PCANBasic):
    trc_files_v1_1[0] = trc_files_v1_1[0].parent / "result_file.trc"

    cc_pcan = CCPCanCan(trace_path=trc_files_v1_1[0])
    cc_pcan._trc_file_names[trc_files_v1_1[0].parent] = []
    for file in trc_files_v1_1:
        cc_pcan._trc_file_names[file.parent].append(file.name)

    result_path = trc_files_v1_1[0]
    cc_pcan._merge_trc()

    with open(result_path, "r") as trc:
        result = trc.read()

    assert trc_data_start_4 + trc_data_end == result


def test_merge_trc_with_multiple_dir(trc_files_different_directory, mock_can_bus, mock_PCANBasic):
    trc_files_different_directory[0] = trc_files_different_directory[0].parent / "result_file.trc"

    cc_pcan = CCPCanCan(trace_path=trc_files_different_directory[0])
    cc_pcan._trc_file_names[trc_files_different_directory[0].parent] = []
    for file in trc_files_different_directory:
        if cc_pcan._trc_file_names.get(file.parent) is None:
            cc_pcan._trc_file_names[file.parent] = []
        cc_pcan._trc_file_names[file.parent].append(file.name)
    result_path = trc_files_different_directory[0]
    result_path_second_dir = trc_files_different_directory[-1]

    cc_pcan._merge_trc()

    # Check if all the trace from the different repo has been merged in one file
    with open(result_path, "r") as trc:
        result = trc.read()
    assert trc_merge_data == result


def test_read_trace_messages(mocker, trc_files, caplog):

    cc_pcan = CCPCanCan(trace_path=trc_files[0])
    cc_pcan.trc_file_version = python_can.TRCFileVersion.V2_0

    mocker.patch.object(CCPCanCan, "_remove_offset", side_effect=["msg1", "msg2"])

    with caplog.at_level(logging.INTERNAL_DEBUG):
        result = cc_pcan._read_trace_messages(trc_files, trc_files[0])

    result_trace = trc_files[0]
    trc_files.pop(0)
    for trc in trc_files:
        assert f"Merging trace {trc.name} into {result_trace.name}" in caplog.text

    assert len(result) == 12
    assert cc_pcan.trc_file_version == python_can.TRCFileVersion.V2_0


def test_read_trace_messages_with_old_file_version(mocker, trc_files_v1_1, caplog):

    cc_pcan = CCPCanCan(trace_path=trc_files_v1_1[0])
    cc_pcan.trc_file_version = python_can.TRCFileVersion.V1_1

    mocker.patch.object(CCPCanCan, "_remove_offset", side_effect=["msg1", "msg2"])

    with pytest.raises(ValueError):
        with caplog.at_level(logging.INTERNAL_WARNING):
            result = cc_pcan._read_trace_messages(trc_files_v1_1, trc_files_v1_1[0])
            assert "Trace merging is not available for trc file version TRCFileVersion.V1_1" in caplog.text


def test_disable_auto_merge(mocker, mock_can_bus, mock_PCANBasic):
    mock_merge = mocker.patch.object(CCPCanCan, "_merge_trc")
    mock_rename = mocker.patch.object(CCPCanCan, "_rename_trc")

    cc_pcan = CCPCanCan(logging_activated=True, merge_trc_logs=True)
    cc_pcan.shutdown()
    mock_merge.assert_called_once()
    mock_rename.assert_not_called()

    mock_merge.reset_mock()
    mock_rename.reset_mock()

    cc_pcan = CCPCanCan(logging_activated=True, merge_trc_logs=False)
    cc_pcan.shutdown()
    mock_merge.assert_not_called()
    mock_rename.assert_called_once()


def test_remove_offset():
    class Msg:
        def __init__(self, timestamp):
            self.timestamp = timestamp

    list_msg = [Msg(10), Msg(15), Msg(20)]
    CCPCanCan._remove_offset(list_msg, 10)
    assert list_msg[0].timestamp == 20
    assert list_msg[1].timestamp == 25
    assert list_msg[2].timestamp == 30


def test_shutdown(mocker, mock_can_bus, mock_PCANBasic):
    cc_pcan = CCPCanCan()
    mock_merge = mocker.patch.object(CCPCanCan, "_merge_trc")

    cc_pcan.logging_activated = False
    cc_pcan.shutdown()
    mock_merge.assert_not_called()

    cc_pcan.logging_activated = True
    cc_pcan.shutdown()
    mock_merge.assert_called_once()


def test_stop_pcan_trace(mocker):
    cc_pcan = CCPCanCan()
    mock_pcan_set_value = mocker.patch.object(CCPCanCan, "_pcan_set_value")
    cc_pcan.trace_running = True

    cc_pcan.stop_pcan_trace()

    mock_pcan_set_value.assert_called_once()
    assert cc_pcan.trace_running is False


def test_start_pcan_trace(mocker):
    cc_pcan = CCPCanCan()
    mock_init_trace = mocker.patch.object(CCPCanCan, "_initialize_trace")
    mock_config_trace = mocker.patch.object(CCPCanCan, "_pcan_configure_trace")

    cc_pcan.start_pcan_trace()

    mock_init_trace.assert_called_once()
    mock_config_trace.assert_called_once()


def test_stop_pcan_trace_already_stopped(caplog):
    cc_pcan = CCPCanCan()
    with caplog.at_level(logging.WARNING):
        cc_pcan.stop_pcan_trace()
    assert "Trace is already stopped" in caplog.text


def test_start_pcan_trace_already_started(caplog):
    cc_pcan = CCPCanCan()
    cc_pcan.trace_running = True
    with caplog.at_level(logging.WARNING):
        cc_pcan.start_pcan_trace()
    assert "Trace is already started" in caplog.text


def test_rename_trace(trc_files, mock_can_bus, mock_PCANBasic):
    # Set the name that should be expected after the rename
    trace_name = ["first_trace_renamed", "second_trace_renamed", "third_trace_renamed"]
    for index, file_name in enumerate(trace_name):
        trc_files[index] = trc_files[index].parent / file_name
    # Setup the ccpcan
    cc_pcan = CCPCanCan(trace_path=trc_files[0])
    cc_pcan.merge_trc_logs = False
    cc_pcan._trc_file_names[trc_files[0].parent] = []
    for file in trc_files:
        cc_pcan._trc_file_names[file.parent].append(file.name)

    cc_pcan._rename_trc()

    for trace, expected_result in zip(
        trc_files,
        [
            trc_data_start_1 + trc_data_end,
            trc_data_start_2 + trc_data_end,
            trc_data_start_3 + trc_data_end,
        ],
    ):
        with open(trace, "r") as trc:
            expected_result = trc.read()


def test_rename_trace_multiple_dir(trc_files_different_directory, mock_can_bus, mock_PCANBasic):
    # Set the new the path that should be expected after the rename
    trace_name = ["first_trace_renamed", "second_trace_renamed", "third_trace_renamed"]
    for index, file_name in enumerate(trace_name):
        trc_files_different_directory[index] = trc_files_different_directory[index].parent / file_name
    # Setup the ccpcan
    cc_pcan = CCPCanCan(trace_path=trc_files_different_directory[0])
    cc_pcan.merge_trc_logs = False
    # Set the path for all trace
    for file in trc_files_different_directory:
        if cc_pcan._trc_file_names.get(file.parent) is None:
            cc_pcan._trc_file_names[file.parent] = []
        cc_pcan._trc_file_names[file.parent].append(file.name)

    cc_pcan._rename_trc()

    # Read the trace file from the path with the rename trace to see if the file has been correctly renamed
    for trace, expected_result in zip(
        trc_files_different_directory,
        [
            trc_data_start_1 + trc_data_end,
            trc_data_start_2 + trc_data_end,
            trc_data_start_3 + trc_data_end,
        ],
    ):
        with open(trace, "r") as trc:
            expected_result = trc.read()
