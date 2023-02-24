import importlib
import sys

import pytest
import serial

from pykiso.lib.connectors import cc_serial
from pykiso.lib.connectors.cc_serial import CCSerial


def test_import():
    with pytest.raises(ImportError):
        sys.modules["serial"] = None
        importlib.reload(cc_serial)
    sys.modules["serial"] = serial
    importlib.reload(cc_serial)


def test_constructor(mocker):

    serial_mock = mocker.patch("serial.Serial")

    cc_serial = CCSerial("com666")

    assert cc_serial.serial.port == "com666"
    serial_mock.assert_called_once()


def test_open_close(mocker):
    serial_mock = mocker.patch("serial.Serial")

    cc_serial = CCSerial("com666")
    cc_serial._cc_open()
    cc_serial._cc_close()

    cc_serial.serial.open.assert_called_once()
    cc_serial.serial.close.assert_called_once()


def test_open_default():
    cc_serial = CCSerial("com666")
    assert cc_serial.serial.is_open is False


def test_receive_one_char(mocker):

    serial_mock = mocker.patch("serial.Serial")

    cc_serial = CCSerial("com666")
    cc_serial.serial.read.return_value = b"s"
    cc_serial.serial.in_waiting = 0

    recv = cc_serial.cc_receive(timeout=0.5)
    assert recv.get("msg") == b"s"
    cc_serial.serial.read.assert_called_once()
    assert cc_serial.serial.timeout == 0


def test_receive_multiple_bytes(mocker):

    serial_mock = mocker.patch("serial.Serial")

    cc_serial = CCSerial("com666")
    cc_serial.serial.read.side_effect = [b"1", b"234"]
    cc_serial.serial.in_waiting = 3

    recv = cc_serial.cc_receive(timeout=0.5)
    assert recv.get("msg") == b"1234"
    assert cc_serial.serial.read.call_count == 2


def test_send(mocker):

    serial_mock = mocker.patch("serial.Serial")

    cc_serial = CCSerial("com666")
    test_chars = b"foo"

    recv = cc_serial.cc_send(test_chars, timeout=666)
    assert cc_serial.serial.write_timeout == 666
    assert cc_serial.current_write_timeout == 666

    cc_serial.serial.write.assert_called_once()
    cc_serial.serial.write.assert_called_with(test_chars)

    recv = cc_serial.cc_send(test_chars, timeout=123)
    assert cc_serial.current_write_timeout == 123
    assert cc_serial.serial.write_timeout == 123
