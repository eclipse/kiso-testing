##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="tests for linux only")

import pathlib
import subprocess
import threading
import time

from pykiso import message
from pykiso.lib.connectors.cc_uart import CCUart


@pytest.fixture
def virtual_serial(tmp_path):
    UART0 = tmp_path / "vt0"
    UART1 = tmp_path / "vt1"
    BAUD = 9600

    uart0 = str(pathlib.Path(UART0).expanduser())
    uart1 = str(pathlib.Path(UART1).expanduser())

    print(f"running 'socat -d -d pty,link={uart0},rawer pty,link={uart1},rawer'")
    socat = subprocess.Popen(
        [
            "/usr/bin/env",
            "socat",
            "-d",
            "-d",
            f"pty,link={uart0},rawer",
            f"pty,link={uart1},rawer",
        ],
    )
    time.sleep(1)  # wait for socat to be up and running
    assert socat.returncode is None
    yield uart0, uart1, BAUD
    socat.terminate()


def _communication_send_check(serial_port, baud):
    """Test to do with HW connected or UART emulator"""
    # message_to_send = message.Message(msg_type=message.MessageType.COMMAND, sub_type=message.MessageCommandType.TEST_CASE_SETUP, test_section=1, test_suite=1, test_case=1)
    message_to_send = message.Message(
        msg_type=message.MessageType.ACK,
        sub_type=message.MessageAckType.ACK,
        test_section=1,
        test_suite=2,
        test_case=3,
    )
    # manually set msg token so it can be checked for
    message_to_send.msg_token = 0
    # Initialize and open uart
    print(f"sending test message to {serial_port}")
    ch = CCUart(serialPort=serial_port, baudrate=baud)
    ch.open()
    # Send message
    ch._cc_send(message_to_send)
    # Close uart
    ch.close()


@pytest.mark.parametrize(
    "timeout, expected_timeout",
    [
        (5, 5),
        (0, 1e-6),
        (None, 1e-6),
    ],
)
def _communication_receive_check(timeout, expected_timeout, serial_port, baud):
    """Test to do with HW connected or UART emulator"""
    message_sent = message.Message(
        msg_type=message.MessageType.COMMAND,
        sub_type=message.MessageCommandType.TEST_CASE_SETUP,
        test_section=1,
        test_suite=2,
        test_case=3,
    )
    # manually set msg token so it matches the received token
    message_sent.msg_token = 0
    # Initialize and open uart
    ch = CCUart(serialPort=serial_port, baudrate=baud)
    ch.open()
    # Wait for a message to be sent: it is C0 78 5E 60 01 00 00 01 02 03 00 C0
    print(f"waiting to receive test message from {serial_port}")
    ack_message_received = ch._cc_receive(timeout=timeout)
    # manually set msg token so it matches the sent token
    ack_message_received.msg_token = 0
    print(f"received: {ack_message_received}")
    # Check validity of the message
    result = message_sent.check_if_ack_message_is_matching(ack_message_received)
    print("Test 2 result: {}".format(result))
    assert result
    assert ch.serial.timeout == expected_timeout
    # Close uart
    ch.close()


def test_virtual_communication(virtual_serial):
    uart0, uart1, BAUD = virtual_serial
    threads = [
        threading.Thread(
            target=_communication_receive_check,
            kwargs=dict(serial_port=uart0, baud=BAUD),
        ),
        threading.Thread(
            target=_communication_send_check,
            kwargs=dict(serial_port=uart1, baud=BAUD),
        ),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
