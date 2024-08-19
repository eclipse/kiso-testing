##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via Serial
********************************

:module: cc_serial

:synopsis: Serial communication channel

.. currentmodule:: cc_serial

"""

import logging
import sys
import time
from enum import Enum, IntEnum
from typing import ByteString, Dict, List, Optional, Union

try:
    import serial
    import serial.tools.list_ports
except ImportError as e:
    raise ImportError(f"{e.name} dependency missing, consider installing pykiso with 'pip install pykiso[serial]'")

log = logging.getLogger(__name__)

from pykiso import Message, connector

MessageType = Union[Message, bytes]


class ByteSize(IntEnum):
    FIVE_BITS = serial.FIVEBITS
    SIX_BITS = serial.SIXBITS
    SEVEN_BITS = serial.SEVENBITS
    EIGHT_BITS = serial.EIGHTBITS


class Parity(str, Enum):
    PARITY_NONE = serial.PARITY_NONE
    PARITY_EVEN = serial.PARITY_EVEN
    PARITY_ODD = serial.PARITY_ODD
    PARITY_MARK = serial.PARITY_MARK
    PARITY_SPACE = serial.PARITY_SPACE


class StopBits(IntEnum):
    STOPBITS_ONE = serial.STOPBITS_ONE
    STOPBITS_ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
    STOPBITS_TWO = serial.STOPBITS_TWO


class CCSerial(connector.CChannel):
    """Connector for serial devices"""

    def __init__(
        self,
        port: Optional[str] = None,
        serial_number: Optional[str] = None,
        vid: Optional[int] = None,
        pid: Optional[int] = None,
        baudrate: int = 9600,
        bytesize: ByteSize = ByteSize.EIGHT_BITS,
        parity: Parity = Parity.PARITY_NONE,
        stopbits: StopBits = StopBits.STOPBITS_ONE,
        timeout: Optional[float] = None,
        xonxoff: bool = False,
        rtscts: bool = False,
        write_timeout: Optional[float] = None,
        dsrdtr: bool = False,
        inter_byte_timeout: Optional[float] = None,
        exclusive: Optional[bool] = None,
        **kwargs,
    ):
        """Init Serial settings

        :param port: Device name (e.g. "COM1" for Windows or "/dev/ttyACM0" for Linux)
        :param serial_number: serial number
        :param vid: vendor id
        :param pid: product id
        :param baudrate: Baud rate such as 9600 or 115200 etc, defaults to 9600
        :param bytesize: Number of data bits. Possible values:
          FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS, defaults to EIGHTBITS
        :param parity: Enable parity checking. Possible values:
          PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE,
          defaults to PARITY_NONE
        :param stopbits:  Number of stop bits. Possible values:
          STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO,
          defaults to STOPBITS_ONE
        :param timeout: Set a read timeout value in seconds, defaults to None
        :param xonxoff: Enable software flow control, defaults to False
        :param rtscts: Enable hardware (RTS/CTS) flow control, defaults to False
        :param write_timeout: Set a write timeout value in seconds, defaults to None
        :param dsrdtr: Enable hardware (DSR/DTR) flow control, defaults to False
        :param inter_byte_timeout:  Inter-character timeout, None to disable,
          defaults to None
        :param exclusive: Set exclusive access mode (POSIX only).
          A port cannot be opened in exclusive access mode if it is already open
          in exclusive access mode., defaults to None
        """

        # Initialize the super class
        super().__init__(**kwargs)
        # Initialize the serial connection. Port None prevents automatic opening
        self.serial = serial.Serial(
            port=None,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive,
        )

        self.current_write_timeout = write_timeout
        self.serial.port = self._get_port(port=port, vid=vid, pid=pid, serial_number=serial_number)

    @staticmethod
    def _find_device(vid: int, pid: int, serial_number: str) -> str:
        """Return the device which matches the given pid/vid or serial_number.

        :param vid: vendor id
        :param pid: product id
        :param serial_number: serial number

        :return: com port for the found device. I.e. "COM4" or "/dev/tty1"
        """

        attached_com_devices = serial.tools.list_ports.comports()
        found_devices = []
        if pid and vid:
            found_devices.extend([port for port in attached_com_devices if port.pid == pid and port.vid == vid])

        if serial_number:
            found_devices.extend([port for port in attached_com_devices if port.serial_number == serial_number])

        if not found_devices:
            raise ConnectionError(
                f"Failed to detect connected USB device with IDs {vid:04X}:{pid:04x} or serial_number {serial_number}."
            )

        found_devices = [port.name if not sys.platform.startswith("win") else port.device for port in found_devices]
        if len(found_devices) > 1:
            log.internal_warning(
                f"Found multiple devices, {found_devices}, with matching IDs {vid:04X}:{pid:04X} or serial_number {serial_number}. Select first device {found_devices[0]}."
            )
        return found_devices[0]

    def _get_port(self, port: str, vid: int, pid: int, serial_number: str) -> str:
        """Returns com port depending on the given port argument.
        If port is None, the device will be searched for,
        using the pid/vid and serial_number, else the port argument will be returned.

        :param port: port  I.e. "COM4" or "/dev/tty1"
        :param vid: vendor id
        :param pid: product id

        :return: com ports of given or found device. I.e. "COM4" or "/dev/tty1"
        """
        if port is None:
            return CCSerial._find_device(vid=vid, pid=pid, serial_number=serial_number)
        else:
            return port

    def _cc_open(self) -> None:
        """Open serial port"""
        self.serial.open()

    def _cc_close(self) -> None:
        """Close serial port"""
        self.serial.close()

    def _cc_send(self, msg: Union[ByteString, str], timeout: float = None, **kwargs) -> None:
        """Sends data to the serial port

        :param msg: data to send
        :param timeout: write timeout in seconds. None sets it to blocking,
          defaults to None
        :param kwargs: not used
        :raises: SerialTimeoutException - In case a write timeout is configured
          for the port and the time is exceeded.
        """
        if timeout != self.current_write_timeout:
            self.current_write_timeout = timeout
            self.serial.write_timeout = timeout

        # Some auxiliaries pass msg as a string
        if isinstance(msg, str):
            msg = msg.encode()

        self.serial.write(msg)

    def _cc_receive(self, timeout=0.00001) -> Dict[str, Optional[bytes]]:
        """Read bytes from the serial port.
        Try to read one byte in blocking mode. After blocking read check
        remaining bytes and read them without a blocking call.

        :param timeout: timeout in seconds, 0 for non blocking read, defaults to 0.00001
        :raises NotImplementedError: if raw is to True
        :return: received bytes
        """

        self.serial.timeout = timeout

        received = self.serial.read()

        # We have waited already so set the timeout to non blocking
        self.serial.timeout = 0

        # Check how many bytes are still left and read them at once
        in_waiting = self.serial.in_waiting
        if in_waiting > 0:
            received += self.serial.read(in_waiting)

        return {"msg": received}
