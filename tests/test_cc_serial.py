import importlib
import logging
import sys
from unittest import mock

import pytest
import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from pykiso.lib.connectors import cc_serial
from pykiso.lib.connectors.cc_serial import CCSerial

# import serial.tools.list_ports_common


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


def test_constructor_auto_port_timeout(mocker):

    serial_mock = mocker.patch("serial.Serial")

    with pytest.raises(ConnectionError):
        CCSerial("auto")


def test_constructor_auto_port(mocker):

    serial_mock = mocker.patch("serial.Serial")
    test_device = ListPortInfo(device="test_device")
    test_device.pid = 1
    test_device.vid = 2
    with mock.patch.object(
        serial.tools.list_ports, "comports", return_value=[test_device]
    ):
        cc_serial = CCSerial(port="auto", pid=1, vid=2)

    assert cc_serial.serial.port == "test_device"
    serial_mock.assert_called_once()


def test_constructor_auto_port_warn(caplog, mocker):

    serial_mock = mocker.patch("serial.Serial")
    test_device = ListPortInfo(device="test_device")
    test_device.pid = 1
    test_device.vid = 2
    test_device2 = ListPortInfo(device="test_device2")
    test_device2.pid = 1
    test_device2.vid = 2
    with mock.patch.object(
        serial.tools.list_ports, "comports", return_value=[test_device, test_device2]
    ):
        with caplog.at_level(logging.WARNING):
            cc_serial = CCSerial(port="auto", pid=1, vid=2)
    assert (
        "Found multiple devices, ['test_device', 'test_device2'], with matching IDs 0002:0001. Select first device test_device."
        in caplog.text
    )
    assert cc_serial.serial.port == "test_device"
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
