##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import logging
import os
import pytest
from can import Message
from can.io.trc import TRCFileVersion
from pathlib import Path

from pykiso.lib.connectors.trc_handler import TypedMessage, TRCReaderCanFD, TRCWriterCanFD

trc_data_v20 = """;$FILEVERSION=2.0
;$STARTTIME=42209.4075997106
;$COLUMNS=N,O,T,I,d,l,D
;
; C:\TraceFile.trc
; Start time: 24.07.2015 09:46:56.615.0
; Generated by PCAN-View v4.0.29.426
;-------------------------------------------------------------------------------
; Connection Bit rate
; PCANLight_USB_16@pcan_usb Nominal 1 MBit/s, Data 2 Mbit/s
;-------------------------------------------------------------------------------
; Message Time Type ID Rx/Tx
; Number Offset | [hex] | Data Length
; | [ms] | | | | Data [hex] ...
; | | | | | | |
;---+-- ------+------ +- --+----- +- +- +- -- -- -- -- -- -- --
1 1059.900 DT 0300 Rx 7 00 00 00 00 04 00 00
2 1283.231 DT 0300 Rx 7 00 00 00 00 04 00 00
3 1298.945 DT 0400 Tx 2 00 00
4 1323.201 DT 0300 Rx 7 00 00 00 00 06 00 00
5 1334.416 FD 0500 Tx 12 01 02 03 04 05 06 07 08 09 0A 0B 0C
6 1334.522 ER Rx 04 00 02 00 00
7 1334.531 ST Rx 00 00 00 08
8 1334.643 EC Rx 02 02
9 1335.156 DT 18EFC034 Tx 8 01 02 03 04 05 06 07 08
10 1336.543 RR 0100 Rx 3"""

trc_data_v21 = """;$FILEVERSION=2.1
;$STARTTIME=41766.4648963872
;$COLUMNS=N,O,T,B,I,d,R,L,D
;
; C:\TraceFile.trc
; Start time: 07.05.2015 11:09:27.047.8
; Generated by PCAN-Explorer v6.0.0
;-------------------------------------------------------------------------------
; Bus Name Connection Protocol
; 1 Connection1 TestNet@pcan_usb CAN
;-------------------------------------------------------------------------------
; Message Time Type ID Rx/Tx
; Number Offset | Bus [hex] | Reserved
; | [ms] | | | | | Data Length Code
; | | | | | | | | Data [hex] ...
; | | | | | | | | |
;---+-- ------+------ +- +- --+----- +- +- +--- +- -- -- -- -- -- -- --
1 1059.900 DT 1 0300 Rx - 7 00 00 00 00 04 00 00
2 1283.231 DT 1 0300 Rx - 7 00 00 00 00 04 00 00
3 1298.945 DT 1 0400 Tx - 2 00 00
4 1323.201 DT 1 0300 Rx - 7 00 00 00 00 06 00 00
5 1334.416 FD 1 0500 Tx - 9 01 02 03 04 05 06 07 08 09 0A 0B 0C
6 1334.222 ER 1 - Rx - 5 04 00 02 00 00
7 1334.224 EV 1 User-defined event for bus 1
8 1334.225 EV - User-defined event for all busses
9 1334.231 ST 1 - Rx - 4 00 00 00 08
10 1334.268 ER 1 - Rx - 5 04 00 02 08 00
11 1334.643 EC 1 - Rx - 2 02 02
12 1335.156 DT 1 18EFC034 Tx - 8 01 02 03 04 05 06 07 08
13 1336.543 RR 1 0100 Rx - 3"""


@pytest.fixture
def trc_file_v20(tmp_path):
    trc_folder = Path(tmp_path / "traces")
    trc_folder.mkdir(parents=True, exist_ok=True)
    file_path = trc_folder / "trc_v20.trc"
    with open(file_path, "w+") as f:
            f.write(trc_data_v20)
            # Sleep to avoid failure on integration tests
        #os.utime(file_path, (1602179630, 1602179630))
    return file_path


@pytest.fixture
def trc_file_v21(tmp_path):
    trc_folder = Path(tmp_path / "traces")
    trc_folder.mkdir(parents=True, exist_ok=True)
    file_path = trc_folder / "trc_v21.trc"
    with open(file_path, "w+") as f:
            f.write(trc_data_v21)
            # Sleep to avoid failure on integration tests
        #os.utime(file_path, (1602179630, 1602179630))
    return file_path


def test_typed_message_constructor():
    msg = Message()
    typed_message = TypedMessage("ST", msg)

    assert typed_message.type == "ST"
    assert typed_message.timestamp ==msg.timestamp
    assert typed_message.arbitration_id == msg.arbitration_id
    assert typed_message.is_extended_id == msg.is_extended_id
    assert typed_message.is_remote_frame == msg.is_remote_frame
    assert typed_message.is_error_frame == msg.is_error_frame
    assert typed_message.channel == msg.channel
    assert typed_message.dlc == msg.dlc
    assert typed_message.data == msg.data
    assert typed_message.is_fd == msg.is_fd
    assert typed_message.is_rx == msg.is_rx
    assert typed_message.bitrate_switch == msg.bitrate_switch
    assert typed_message.error_state_indicator == msg.error_state_indicator
    assert typed_message._check == msg._check


def test_typed_message_repr():
    msg = Message()
    typed_message = TypedMessage("DT", msg)

    assert typed_message.__repr__() == 'can.Message(timestamp=0.0, arbitration_id=0x0, is_extended_id=True, dlc=0, data=[])'

    msg.is_rx = False
    msg.is_remote_frame = True
    msg.is_error_frame = True
    msg.channel = 1
    msg.is_fd = True
    typed_message_error_frame = TypedMessage("ER", msg)

    result_error_frame = "can.Message(timestamp=0.0, arbitration_id=0, is_extended_id=True, is_rx=False, is_remote_frame=True, is_error_frame=True, channel=1, dlc=0, data=[], is_fd=True, bitrate_switch=False, error_state_indicator=False)"
    assert typed_message_error_frame.__repr__() == result_error_frame


@pytest.mark.parametrize(
    "file_version, cols, nomalized_cols",
    [
        (TRCFileVersion.V2_0, ['1', '639.182', 'ST', 'Rx', '00', '00', '00', '00'], ['1', '639.182', 'ST', '    ', 'Rx', ' ', '00', '00', '00', '00']),
        (TRCFileVersion.V2_1, ['1', '639.182', 'ST', 'Rx', '00', '00', '00', '00'], ['1', '639.182', 'ST', '   -', 'Rx', ' ', '00', '00', '00', '00']), 
        (TRCFileVersion.V2_0, ['31', '5862.939', 'FD', '0123', 'Tx', '8', '02', '3E', '80', '00', '00', '00', '00', '00'], ['31', '5862.939', 'FD', '0123', 'Tx', '8', '02', '3E', '80', '00', '00', '00', '00', '00']),
    ],
)
def test_trc_reader_can_fd_nomalize_cols(trc_file_v20, trc_file_v21, file_version, cols, nomalized_cols):

    if file_version == TRCFileVersion.V2_0:
        my_reader = TRCReaderCanFD(trc_file_v20)
    else: 
        my_reader = TRCReaderCanFD(trc_file_v21)
        
    my_reader.file_version = file_version
    my_reader.columns = {'N': 0, 'O': 1, 'T': 2, 'I': 3, 'd': 4, 'L': 5, 'D': 6}

    result = my_reader._nomalize_cols(cols)
    assert result == nomalized_cols


@pytest.mark.parametrize(
    "cols",
    [
        (['1', '639.182', 'ST', '    ', 'Rx', ' ', '00', '00', '00', '00']),
        (['31', '5862.939', 'NA', '0123', 'Tx', '8', '02', '3E', '80', '00', '00', '00', '00', '00']),
    ],
)
def test_trc_reader_can_fd_parse_cols_V2_x(mocker, trc_file_v20, cols, caplog):
    my_reader = TRCReaderCanFD(trc_file_v20)
    my_reader.columns = {'N': 0, 'O': 1, 'T': 2, 'I': 3, 'd': 4, 'L': 5, 'D': 6}

    mocker.patch.object(
        TRCReaderCanFD, "_nomalize_cols", return_value=cols
    )
    mocker.patch.object(
        TRCReaderCanFD, "_parse_msg_V2_x", return_value="result"
    )
    with caplog.at_level(logging.INFO):
        result = my_reader._parse_cols_V2_x(cols)
    
    TRCReaderCanFD._nomalize_cols.assert_called_once_with(cols)
    type = cols[my_reader.columns["T"]]
    if type == "NA":
        assert (
            f"TRCReader: Unsupported type '{type}'\n"
            in caplog.text
        )
        assert result == None
        TRCReaderCanFD._parse_msg_V2_x.assert_not_called()
    else: 
        TRCReaderCanFD._parse_msg_V2_x.assert_called_once_with(cols)
        assert result == "result"

@pytest.mark.parametrize(
    "file_version, cols, expected_result",
    [
        (TRCFileVersion.V2_0, ['1', '639.182', 'ST', '    ', 'Rx', ' ', '00', '00', '00', '00'], ("ST", 0.639182, '    ', False, 1, 4, bytearray(b'\x00\x00\x00\x00'), True, False, False, False, False, False)),
        (TRCFileVersion.V2_0, ['1', '639.182', 'ER', '    ', 'Rx', ' ', '00', '00', '00', '00', '00'], ("ER", 0.639182, '    ', False, 1, 5,  bytearray(b'\x00\x00\x00\x00\x00'), True, False, False, False, True, False)),
        (TRCFileVersion.V2_0, ['1', '639.182', 'EC', '    ', 'Rx', ' ', '00', '00'], ("EC", 0.639182, '    ', False, 1, 2,  bytearray(b'\x00\x00'), True, False, False, False, False, False)),
        (TRCFileVersion.V2_0, ['1', '639.182', 'FD', '0200', 'Tx', '4', '00', '00', '00', '00'], ("FD", 0.639182, 512, False, 1, 4,  bytearray(b'\x00\x00\x00\x00'), False, True, False, False, False, False)),
        (TRCFileVersion.V2_1, ['1', '639.182', 'ST', '0200', 'Rx', '4', '00', '00', '00', '00'], ("ST", 0.639182, 512, False, 1, 4, bytearray(b'\x00\x00\x00\x00'), True, False, False, False, False, False)),
        (TRCFileVersion.V2_1, ['1', '639.182', 'ER', '0200', 'Rx', '5', '00', '00', '00', '00', '00'], ("ER", 0.639182, 512, False, 1, 5,  bytearray(b'\x00\x00\x00\x00\x00'), True, False, False, False, True, False)),
        (TRCFileVersion.V2_1, ['1', '639.182', 'EC', '0200', 'Rx', '2', '00', '00'], ("EC", 0.639182, 512, False, 1, 2,  bytearray(b'\x00\x00'), True, False, False, False, False, False)),
        (TRCFileVersion.V2_1, ['1', '639.182', 'FD', '0200', 'Rx', '4', '00', '00', '00', '00'], ("FD", 0.639182, 512, False, 1, 4,  bytearray(b'\x00\x00\x00\x00'), True, True, False, False, False, False))
    ],
)
def test_trc_reader_can_fd_parse_msg_V2_x(trc_file_v20, trc_file_v21, file_version, cols, expected_result):
    
    if file_version == TRCFileVersion.V2_0:
        my_reader = TRCReaderCanFD(trc_file_v20)
    else: 
        my_reader = TRCReaderCanFD(trc_file_v21)
        
    my_reader.file_version = file_version
    my_reader.columns = {'N': 0, 'O': 1, 'T': 2, 'I': 3, 'd': 4, 'L': 5, 'D': 6}

    result_msg = my_reader._parse_msg_V2_x(cols)

    assert result_msg.type == expected_result[0]
    assert result_msg.timestamp == expected_result[1]
    assert result_msg.arbitration_id == expected_result[2]
    assert result_msg.is_extended_id == expected_result[3]         
    assert result_msg.channel == expected_result[4]
    assert result_msg.dlc == expected_result[5]
    assert result_msg.data == expected_result[6]   
    assert result_msg.is_rx == expected_result[7] 
    assert result_msg.is_fd == expected_result[8]                             
    assert result_msg.bitrate_switch == expected_result[9]
    assert result_msg.error_state_indicator == expected_result[10]
    assert result_msg.is_error_frame == expected_result[11]
    assert result_msg.is_remote_frame == expected_result[12]


