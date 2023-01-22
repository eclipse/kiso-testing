##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import importlib
import sys

import pytest
import serial

from pykiso import message
from pykiso.lib.connectors import cc_uart
from pykiso.lib.connectors.cc_uart import CCUart, IncompleteCCMsgError


@pytest.fixture
def CCuart_instance():
    return CCUart(serialPort="port")


@pytest.fixture
def serial_read_mock(mocker):
    return mocker.patch("serial.Serial.read")


def test_import():
    with pytest.raises(ImportError):
        sys.modules["serial"] = None
        importlib.reload(cc_uart)
    sys.modules["serial"] = serial
    importlib.reload(cc_uart)


def test_incomplete_ccmsg_error():
    value = 12
    msg_error = IncompleteCCMsgError(value)

    assert str(msg_error) == "12"


def test__cc_open(CCuart_instance, mocker):
    open_serial_mock = mocker.patch("serial.Serial.open")

    CCuart_instance._cc_open()

    open_serial_mock.assert_called_once_with()


def test__cc_close(CCuart_instance, mocker):
    close_serial_mock = mocker.patch("serial.Serial.close")

    CCuart_instance._cc_close()

    close_serial_mock.assert_called_once_with()


def test__cc_send(mocker, CCuart_instance):
    msg = message.Message()
    _send_using_slip_mock = mocker.patch.object(CCuart_instance, "_send_using_slip")

    CCuart_instance._cc_send(msg)

    _send_using_slip_mock.assert_called_once()


def test__cc_receive_no_msg(CCuart_instance, serial_read_mock):
    serial_read_mock.return_value = []

    msg = CCuart_instance._cc_receive()

    serial_read_mock.assert_called_once_with(1)
    assert msg is None


def test__cc_receive_not_expexted_crc32(CCuart_instance, serial_read_mock):
    serial_read_mock.side_effect = [
        (0xC0,),
        (0xC0,),
        (CCUart.ESC,),
        (CCUart.ESC_START,),
        (CCUart.ESC,),
        (CCUart.ESC_ESC,),
    ] + [(0x0,)] * 10

    msg = CCuart_instance._cc_receive()

    assert serial_read_mock.call_count == 14
    assert msg is None


def test__cc_receive_expexted_crc32(CCuart_instance, serial_read_mock):
    serial_read_mock.side_effect = [(0xC0,), (0xC0,)] + [(0x0,)] * 10

    msg = CCuart_instance._cc_receive()

    assert serial_read_mock.call_count == 12
    assert msg is not None


@pytest.mark.parametrize(
    "raw_packet,bytes_expected,call_count",
    [([0xC0], CCUart.ESC_START, 3), ([0xDB], CCUart.ESC_ESC, 3), ([0x12], 0x12, 2)],
)
def test__send_using_slip(
    CCuart_instance, mocker, raw_packet, bytes_expected, call_count
):
    write_mocker = mocker.patch("serial.Serial.write")
    flush_output_mock = mocker.patch("serial.Serial.flushOutput")

    CCuart_instance._send_using_slip(raw_packet)

    assert write_mocker.call_count == call_count
    write_mocker.assert_called_with(bytes_expected.to_bytes(1, byteorder="big"))
    flush_output_mock.assert_called_once()
