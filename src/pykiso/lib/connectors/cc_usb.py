##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via Usb
********************************

:module: cc_usb

:synopsis: Usb communication channel

.. currentmodule:: cc_usb


.. warning: Still under test
"""

import serial

from pykiso.lib.connectors import cc_uart


class CCUsb(cc_uart.CCUart):
    def __init__(self, serial_port):
        super().__init__(serial_port, baudrate=9600)

    def _cc_send(self, msg):

        raw_packet = msg.serialize()
        crc = self._calculate_crc32(raw_packet)

        raw_packet.insert(0, ((crc >> 8) & 0xFF))
        raw_packet.insert(1, (crc & 0xFF))
        self._send_using_slip(raw_packet)

    def _send_using_slip(self, raw_packet):
        slip_raw_packet = []
        slip_raw_packet.append(self.START)

        for a_byte in raw_packet:
            if a_byte == self.START:
                slip_raw_packet.append(self.ESC)
                slip_raw_packet.append(self.ESC_START)
            elif a_byte == self.ESC:
                slip_raw_packet.append(self.ESC)
                slip_raw_packet.append(self.ESC_ESC)
            else:
                slip_raw_packet.append(a_byte)
        self.serial.write(bytearray(slip_raw_packet))
        self.serial.flushOutput()
        return

    #################### todo TO DELETE IF NOT NEEDED ANYMORE #######################

    def CCwaitAfterReboot(self, retry_count, reboot_time):
        import time

        self.CCclose()
        for i in range(retry_count):
            try:
                time.sleep(reboot_time)
                self.CCopen()
                break
            except (serial.SerialException, serial.serialutil.SerialTimeoutException):
                self.logger.debug(
                    "Unable to connect to USB port after reboot."
                    + "Retrying after "
                    + reboot_time
                    + " seconds"
                )
