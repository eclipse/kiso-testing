##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via Uart
********************************

:module: cc_uart

:synopsis: Uart communication channel

.. currentmodule:: cc_uart

"""

import struct
import time
from typing import Optional

import serial

from pykiso import connector, message


class IncompleteCCMsgError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class CCUart(connector.CChannel):
    """UART implementation of the coordination channel."""

    headerSize = 8
    payloadLengthIndex = 7

    WAITING_FOR_START = 0
    RECEIVING_HEADER = 1
    RECEIVING_PAYLOAD = 2
    RECEIVED_DONE = 3

    START = 0xC0
    ESC = 0xDB
    ESC_START = 0xDC
    ESC_ESC = 0xDD

    def __init__(self, serialPort, baudrate=9600, **kwargs):
        # Initialize the super class
        super().__init__(**kwargs)
        # Initialize the serial connection
        self.serial = serial.Serial(timeout=1)
        self.serial.port = serialPort
        self.serial.baudrate = baudrate
        self.serial.paritiy = serial.PARITY_NONE
        # Set a timeout to send the signal to the GIL to change thread.
        # In case of a multi-threading system, all tasks will be called one after the other.
        self.timeout = 1e-6

    def _cc_open(self):
        self.serial.open()

    def _cc_close(self):
        self.serial.close()

    def _cc_send(self, msg):
        rawPacket = msg.serialize()
        # Use CRC to verify content
        crc = self._calculate_crc32(rawPacket)
        rawPacket = struct.pack(">H", crc) + rawPacket  # Force big endian notation
        self._send_using_slip(rawPacket)

    def _cc_receive(self, timeout=0.00001):

        self.serial.timeout = timeout or self.timeout

        receivingState = self.WAITING_FOR_START
        bytesToRead = 10
        rawPacket = []

        while bytesToRead > 0:
            singleByteRead = self.serial.read(1)

            if 0 == len(singleByteRead):
                return None

            if self.WAITING_FOR_START == receivingState:
                if self.START == singleByteRead[0]:
                    receivingState = self.RECEIVING_HEADER
            else:
                if self.START == singleByteRead[0]:
                    bytesToRead = 10
                    rawPacket = []
                    receivingState = self.RECEIVING_HEADER
                    # TODO: dei9bue something went wrong
                else:
                    bytesToRead -= 1

                    if self.ESC == singleByteRead[0]:
                        singleByteRead = self.serial.read(1)

                        if self.ESC_START == singleByteRead[0]:
                            rawPacket.append(self.START)
                        elif self.ESC_ESC == singleByteRead[0]:
                            rawPacket.append(self.ESC)
                    else:
                        rawPacket.append(singleByteRead[0])

                if 0 == bytesToRead:
                    if self.RECEIVING_HEADER == receivingState:
                        bytesToRead = singleByteRead[0]
                        if bytesToRead:
                            receivingState = self.RECEIVING_PAYLOAD
                        else:
                            receivingState = self.RECEIVED_DONE
                    elif self.RECEIVING_PAYLOAD == receivingState:
                        receivingState = self.RECEIVED_DONE

            if receivingState == self.RECEIVED_DONE:

                expectedCRC = ((rawPacket[0] & 0xFF) << 8) + (rawPacket[1] & 0xFF)
                rawPacket = rawPacket[2 : len(rawPacket)]
                calculatedCRC = self._calculate_crc32(rawPacket)

                if calculatedCRC != expectedCRC:
                    return None
        # Reception was a success, we need now to convert the list into a array of bytes
        binary_message = b"".join(struct.pack("B", value) for value in rawPacket)
        return message.Message.parse_packet(binary_message)

    def _send_using_slip(self, rawPacket):
        self.serial.write(self.START.to_bytes(1, byteorder="big"))

        for aByte in rawPacket:
            if aByte == self.START:
                self.serial.write(self.ESC.to_bytes(1, byteorder="big"))
                self.serial.write(self.ESC_START.to_bytes(1, byteorder="big"))
            elif aByte == self.ESC:
                self.serial.write(self.ESC.to_bytes(1, byteorder="big"))
                self.serial.write(self.ESC_ESC.to_bytes(1, byteorder="big"))
            else:
                self.serial.write(aByte.to_bytes(1, byteorder="big"))

        time.sleep(0.01)
        self.serial.flushOutput()
        return

    def _calculate_crc32(self, buffer):
        crc = 0

        CRC_BIT_SHIFT_4 = 4
        CRC_BIT_SHIFT_5 = 5
        CRC_BIT_SHIFT_8 = 8
        CRC_BIT_SHIFT_12 = 12
        CRC_BYTE_MASK = 0xFF

        for aByte in buffer:
            crc = ((crc >> (CRC_BIT_SHIFT_8)) | (crc << (CRC_BIT_SHIFT_8))) & 0xFFFF
            crc = (crc ^ (aByte & CRC_BYTE_MASK)) & 0xFFFF
            crc = (crc ^ (crc & (CRC_BYTE_MASK)) >> (CRC_BIT_SHIFT_4)) & 0xFFFF
            crc = (crc ^ ((crc << (CRC_BIT_SHIFT_12)) & 0xFFFF)) & 0xFFFF
            crc = (crc ^ (crc & (CRC_BYTE_MASK)) << (CRC_BIT_SHIFT_5)) & 0xFFFF

        return crc & 0xFFFF
