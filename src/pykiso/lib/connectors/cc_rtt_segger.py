##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via segger j-link
***************************************

:module: cc_rtt_segger

:synopsis: channel used to enable RTT communication using Segger J-Link debugger.
    Additionally, RTT logs can be captured by setting the rtt_log_path parameter
    on the specified channel.

.. currentmodule:: cc_rtt_segger

"""
import functools
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Union

import pylink

from pykiso import connector
from pykiso.message import Message

log = logging.getLogger(__name__)


def _need_connection(f):
    """Decorator to check the JLink is connected and raises an error otherwise"""

    @functools.wraps(f)
    def check_before_execution(self, *args, **kwargs):
        """Check if Jlink is opened, else raise error

        :raises pylink.JLinkException: if Jlink not available
        """
        if not self.jlink.opened():
            raise pylink.JLinkException("You need to connect to a JLink first")
        return f(self, *args, **kwargs)

    return check_before_execution


def _need_rtt(f):
    """Decorator to check that a RTT connection has been configured and raises an error otherwise"""

    @functools.wraps(f)
    def check_before_execution(self, *args, **kwargs):
        """Check if Jlink is opened and RTT configured, else raise errors

        :raises pylink.JLinkException: if RTT config not done or Jlink not available
        """

        if not self.jlink.opened():
            raise pylink.JLinkException("You need to connect to a JLink first")
        if not self.rtt_configured:
            raise pylink.JLinkException("You need to configure RTT first")
        return f(self, *args, **kwargs)

    return check_before_execution


class CCRttSegger(connector.CChannel):
    """Channel using RTT to communicate through Segger J-Link debugger."""

    def __init__(
        self,
        serial_number: int = None,
        chip_name: str = "STM32L562QE",
        speed: int = 4000,
        block_address: int = 0x2003F800,
        verbose: bool = False,
        tx_buffer_idx: int = 3,
        rx_buffer_idx: int = 0,
        rtt_log_path: Optional[str] = None,
        rtt_log_buffer_idx: int = 0,
        rtt_log_speed: float = 1000,
        connection_timeout: int = 5,
        **kwargs,
    ):
        """Initialize attributes.

        :param serial_number: optional segger debugger serial number (required if many connected)
        :param chip_name: microcontoller name (STM....)
        :param speed: communication speed in Hz
        :param block_address: start address to start RTT communication
        :param tx_buffer_idx: buffer index used for transmission
        :param rx_buffer_idx: buffer index used for reception
        :param verbose: boolean indicating if J-Link connection should be verbose in logging
        :param rtt_log_path: path to the folder where the RTT log file should be stored
        :param rtt_log_buffer_idx: buffer index used for RTT logging
        :param rtt_log_speed: number of log per second to be pulled (manage the CPU load for logging)
            None value fetch log at the CPU's speed. Default 1000 logs/s
        :param connection_timeout: available time (in seconds) to open the connection
        """
        super().__init__(**kwargs)
        self.serial_number = serial_number if isinstance(serial_number, int) else None
        self.chip_name = chip_name
        self.speed = speed
        self.block_address = block_address
        self.tx_buffer_idx = tx_buffer_idx
        self.rx_buffer_idx = rx_buffer_idx
        self.verbose = verbose
        self.jlink = None
        self.connection_timeout = connection_timeout
        self.rtt_log_buffer_idx = rtt_log_buffer_idx
        self.rx_buffer_size = None
        # initialize rtt logging specific parameters
        self.rtt_configured = False
        self._log_thread_running = False
        self.rtt_log_refresh_time = round(1 / rtt_log_speed, 6) if rtt_log_speed else 0
        self.rtt_log_thread = threading.Thread(target=self.receive_log)
        self.rtt_log_path = rtt_log_path
        self.rtt_log = logging.getLogger(f"{__name__}{serial_number or ''}.RTT")
        if self.rtt_log_path is not None:
            self.rtt_log_buffer_size = 0
            self.rtt_log_path = Path(rtt_log_path)
            # if log folder does not exists create it during process
            self.rtt_log_path.mkdir(parents=True, exist_ok=True)
            rtt_fh = logging.FileHandler(self.rtt_log_path / "rtt.log")
            rtt_fh.setLevel(logging.DEBUG)
            self.rtt_log.setLevel(logging.DEBUG)
            self.rtt_log.addHandler(rtt_fh)

    def read_target_memory(
        self, addr: int, num_units: int, zone: str = None, nbits: int = 32
    ) -> Optional[list]:
        """Read the given target's memory units and the given address.

        .. note:: The optional ``zone`` specifies a memory zone to
            access to read from, e.g. ``IDATA``, ``DDATA``, or ``CODE``.

        .. warning:: The given number of bits, if provided, must be
            either ``8``, ``16``, or ``32``.  If not provided, always
            reads 32 bits.

        :param addr: start address to read from
        :param num_units: number of units to read
        :param zone: optional memory zone name to access
        :param nbits: number of bits to use for each unit

        :return: List of units read from the target.
        """
        mem_vals = None

        try:
            mem_vals = self.jlink.memory_read(addr, num_units, zone, nbits)
        except pylink.errors.JLinkException:
            log.exception(f"encountered error while reading memory at {hex(addr)}")
        except ValueError:
            log.exception("wrong number of bits given : must be 8, 16 or 32 bits")

        return mem_vals

    def _cc_open(self) -> None:
        """Connect debugger/microcontroller.

        This method proceed to the following actions :
        - create a JLink class instance
        - connect to  the debugger(using open method)
        - set debugger interface to SWD
        - connect debugger to the specified chip
        - start RTT communication
        - start RTT Logging the specified channel if activated

        :raise JLinkRTTException: if connection timeout occurred.
        """
        self.jlink = pylink.JLink()

        # connect to J-Link debugger
        if not self.jlink.opened():
            self.jlink.open(self.serial_number)
            log.internal_info(
                f"connection made with J-Link debugger {self.serial_number}"
            )
        else:
            log.internal_debug("connection to J-Link already started")
        # set target interface to SWD
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        # connect debugger to  the specified target
        self.jlink.connect(
            chip_name=self.chip_name, speed=self.speed, verbose=self.verbose
        )
        log.internal_debug(
            f"connection to chip {self.chip_name} performed at speed {self.speed}Hz"
        )
        # reset debugger if halted
        if self.jlink.halted():
            log.internal_info(
                f"J-Link is halted, reset target and wait for {self.connection_timeout}s"
            )
            self.jlink.reset(halt=False)
            time.sleep(self.connection_timeout)
        # start rtt at the specified address
        self.jlink.rtt_start(self.block_address)
        log.internal_info(f"RTT communication started at address {self.block_address}")

        t_start = time.perf_counter()
        while True:
            try:
                num_up = self.jlink.rtt_get_num_up_buffers()
                num_down = self.jlink.rtt_get_num_down_buffers()
                log.internal_debug(
                    f"RTT started. Found {num_up} up and {num_down} down channels."
                )
                # get rx buffer size
                rx_buffer = self.jlink.rtt_get_buf_descriptor(self.rx_buffer_idx, True)
                self.rx_buffer_size = rx_buffer.SizeOfBuffer
                log.internal_debug(
                    f"Maximum size for a received message set to {self.rx_buffer_size}"
                )
                self.rtt_configured = True
                break
            except pylink.errors.JLinkRTTException:
                time.sleep(0.1)
                # Exit the while loop once timeout is reached
                if time.perf_counter() > (t_start + self.connection_timeout):
                    raise

        # start rtt logging thread on buffer index rtt_log_buffer_idx
        if self.rtt_log_path is not None:
            try:
                rtt_log_buffer = self.jlink.rtt_get_buf_descriptor(
                    self.rtt_log_buffer_idx, True
                )
                self.rtt_log_buffer_size = rtt_log_buffer.SizeOfBuffer
                if self.rtt_log_buffer_size == 0:
                    raise ValueError
                log.internal_debug(
                    f"RTT log buffer size is {self.rtt_log_buffer_size} bytes"
                )
            except ValueError:
                log.internal_debug("Read RTT log buffer size is 0, defaulting to 1kB")
                self.rtt_log_buffer_size = 1024
            except pylink.errors.JLinkRTTException as e:
                log.error(f"Could not get RTT log buffer size: {e}")
                if self.rtt_log_buffer_idx not in range(num_up + 1):
                    log.error(f"Buffer index must be at most {num_up}")
                    self.rtt_log_buffer_idx = 0
                self.rtt_log_buffer_size = 1024
            finally:
                self._log_thread_running = True
                self.rtt_log_thread.start()
                log.internal_info("RTT logging started")

    def _cc_close(self) -> None:
        """Close current RTT communication in use."""

        if self.jlink is not None:
            if self._log_thread_running:
                self._log_thread_running = False
                self.rtt_log_thread.join()
            self.jlink.rtt_stop()
            self.jlink.close()
            log.internal_info("RTT communication closed")

    def _cc_send(self, msg: bytes) -> None:
        """Send message using the corresponding RTT buffer.

        :param msg: message to send, should be bytes.
        """
        try:

            msg = list(msg)
            bytes_written = self.jlink.rtt_write(self.tx_buffer_idx, msg)
            log.internal_debug(
                "===> message sent (RTT) on buffer %d: %s, number of bytes written: %d",
                self.tx_buffer_idx,
                msg,
                bytes_written,
            )
        except Exception:
            log.exception(
                f"ERROR occurred while sending {len(msg)} bytes on buffer {self.tx_buffer_idx}"
            )

    def _cc_receive(
        self, timeout: float = 0.1, size: int = None, **kwargs
    ) -> Dict[str, Optional[bytes]]:
        """Read message from the corresponding RTT buffer.

        :param timeout: timeout applied on receive event
        :param size: maximum amount of bytes to read
        :return: dictionary containing the received bytes if successful, otherwise None
        """
        is_timeout = False
        # maximum amount of bytes to read out
        size = size or self.rx_buffer_size
        t_start = time.perf_counter()

        # rtt_read is not a blocking method due to this fact a while loop is used
        # to act like a blocking ones.
        while not is_timeout:
            try:
                # Read the message header or all of the buffer
                msg_received = self.jlink.rtt_read(self.rx_buffer_idx, size)
                # if a message is received
                if msg_received:
                    # Parse the bytes list into bytes string
                    msg_received = bytes(msg_received)
                    log.internal_debug(
                        "<=== message received (RTT) on buffer %d: %s, number of bytes read: %d",
                        self.rx_buffer_idx,
                        msg_received,
                        len(msg_received),
                    )
                    break
            except Exception:
                log.exception(
                    f"encountered error while receiving message via {self} on buffer {self.rx_buffer_idx}"
                )
                return {"msg": None}

            # Exit the while loop once timeout is reached
            if time.perf_counter() > (t_start + timeout):
                is_timeout = True
                msg_received = None

        return {"msg": msg_received}

    @_need_rtt
    def receive_log(self) -> None:
        """Receive RTT log messages from the corresponding RTT buffer."""
        while self._log_thread_running:
            # receive at most rtt_log_buffer_size of RTT logs
            log_msg = self.jlink.rtt_read(
                self.rtt_log_buffer_idx, self.rtt_log_buffer_size
            )
            if log_msg:
                self.rtt_log.internal_debug(bytes(log_msg).decode())
            time.sleep(self.rtt_log_refresh_time)  # reduce resource consumption

    @_need_connection
    def reset_target(self, wait_time: int = 100, halt: bool = False) -> None:
        """Reset target via JLink.

        :param wait_time: Amount of milliseconds to delay after reset
        :param halt: if the CPU should halt after reset
        """
        logging.info("Reset Target")
        self.jlink.enable_reset_pulls_reset()
        self.jlink.reset(wait_time, halt)
