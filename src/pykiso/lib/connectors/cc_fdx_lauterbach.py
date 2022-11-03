##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via lauterbach
************************************

:module: cc_fdx_lauterbach

:synopsis: CChannel implementation for lauterbach(FDX)

.. currentmodule:: cc_fdx_lauterbach

"""

import ctypes
import enum
import logging
import subprocess
import time
from typing import Dict, Optional, Union

from pykiso import connector
from pykiso.message import Message

log = logging.getLogger(__name__)


class PracticeState(enum.IntEnum):
    """Available state for any scripts loaded into TRACE32."""

    UNKNOWN = -1
    NOT_RUNNING = 0
    RUNNING = 1
    DIALOG_OPEN = 2


class CCFdxLauterbach(connector.CChannel):
    """Lauterbach connector using the FDX protocol."""

    def __init__(
        self,
        t32_exc_path: str = None,
        t32_config: str = None,
        t32_main_script_path: str = None,
        t32_reset_script_path: str = None,
        t32_fdx_clr_buf_script_path: str = None,
        t32_in_test_reset_script_path: str = None,
        t32_api_path: str = None,
        port: str = None,
        node: str = "localhost",
        packlen: str = "1024",
        device: int = 1,
        **kwargs,
    ):
        """Constructor: initialize attributes with configuration data.

        :param t32_exc_path: full path of Trace32 app to execute
        :param t32_config: full path of Trace32 configuration file
        :param t32_main_script_path: full path to the main cmm script to execute
        :param t32_reset_script_path: full path to the reset cmm script to execute
        :param t32_fdx_clr_buf_script_path: full path to the FDX reset cmm script to execute
        :param t32_in_test_reset_script_path: full path to the board reset cmm script to execute
        :param t32_api_path: full path of remote api
        :param port: port number used for UDP communication
        :param node: node name (default localhost)
        :param packlen: data pack length for UDP communication (default 1024)
        :param device: configure device number given by Trace32 (default 1)
        """
        self.t32_main_script_path = t32_main_script_path
        self.t32_reset_script_path = t32_reset_script_path
        self.t32_fdx_clr_buf_script_path = t32_fdx_clr_buf_script_path
        self.t32_in_test_reset_script_path = t32_in_test_reset_script_path
        self.t32_api_path = t32_api_path
        self.t32_start_args = [t32_exc_path, "-c", t32_config]
        self.port = str(port)
        self.node = str(node)
        self.packlen = str(packlen)
        self.device = device
        self.t32_process = None
        self.t32_api = None
        self.loadup_wait_time = 4
        self.fdxin = -1
        self.fdxout = -1
        self.reset_flag = False
        self.safe_reset_flag = False
        self.allowed_t32_errors = 10
        # Initialize the super class
        super().__init__(**kwargs)

    def load_script(self, script_path: str):
        """Load a cmm script.

        :param script_path: cmm file path

        :return: error status
        """
        err = 0

        # Run the script
        err = self.t32_api.T32_Cmd(f"DO {script_path}".encode())
        if err != 0:
            log.error(f"Error '{err}' while loading the cmm file: {script_path}")
            return err
        log.internal_info(f"Loading the cmm file: {script_path}")

        # Check whether the scrip we just launched has completed or not.
        state = ctypes.c_int(PracticeState.UNKNOWN)
        error_count = 0
        while not state.value == PracticeState.NOT_RUNNING:
            err = self.t32_api.T32_GetPracticeState(ctypes.byref(state))
            if err != 0:
                error_count += 1
            if error_count >= self.allowed_t32_errors:
                log.error(
                    f"Abort execution because lauterbach was unresponsive for {error_count} times"
                )
                break
            time.sleep(0.05)  # 50 ms pause in each loop

        if err != 0:
            log.error("Error occurred while checking the script state")

        return err

    def _cc_open(self) -> bool:
        """Load the Trace32 library, open the application and open the FDX channels (in/out).

        :return: True if Trace32 is correctly open otherwise False
        """
        lauterbach_open_state = False

        # Load Trace32 remote api library
        try:
            self.t32_api = ctypes.CDLL(self.t32_api_path)
            log.internal_debug("Trace32 remote API loaded")
        except Exception as e:
            log.exception(f"Unable to open Trace32: {e}")
            return lauterbach_open_state

        # Looking for an active Trace32 process and close it
        if self.t32_api.T32_Init() == 0:
            # Quit properly the previous T32 instance
            self.t32_api.T32_Cmd("QUIT".encode("latin-1"))
            log.internal_debug("Previous process Trace32 closed")

        # Open a new Trace32 process
        try:
            self.t32_process = subprocess.Popen(self.t32_start_args)
            log.internal_debug(
                f"Trace32 process open with arguments {self.t32_start_args}"
            )
        except Exception:
            log.exception("Unable to open Trace32")
            return lauterbach_open_state

        # Wait until Trace32 app is launched
        time.sleep(self.loadup_wait_time)

        # Set channel configuration
        self.t32_api.T32_Config(b"NODE=", self.node.encode("utf-8"))
        self.t32_api.T32_Config(b"PORT=", self.port.encode("utf-8"))
        self.t32_api.T32_Config(b"PACKLEN=", self.packlen.encode("utf-8"))

        # Open UDP connection with Trace32
        self.t32_api.T32_Init()
        self.t32_api.T32_Attach(self.device)

        # Ping
        if self.t32_api.T32_Ping() == 0:
            log.internal_debug(f"ITF connected on {self.node}:{self.port}")
        else:
            log.fatal(f"Unable to connect on port :{self.port}")
            return lauterbach_open_state

        # Clear the FDX buffer if script provided
        if self.load_script(self.t32_fdx_clr_buf_script_path) == 0:
            log.internal_info(f"script {self.t32_fdx_clr_buf_script_path} loaded")

        # Load the cmm script
        if self.load_script(self.t32_main_script_path) == 0:
            log.internal_debug(f"script {self.t32_main_script_path} loaded")
        else:
            log.fatal(f"Unable to load {self.t32_main_script_path}")
            return lauterbach_open_state

        # Get FDX receiver channel
        self.fdxin = self.t32_api.T32_Fdx_Open(b"FdxTestSendBuffer", b"r")
        if self.fdxin == -1:
            log.fatal("No FDXin buffer")
            return lauterbach_open_state

        # Get FDX sender channel
        self.fdxout = self.t32_api.T32_Fdx_Open(b"FdxTestReceiveBuffer", b"w")
        if self.fdxout == -1:
            log.fatal("No FDXout buffer")
            return lauterbach_open_state

        # Run the script
        self.start()

        lauterbach_open_state = True
        return lauterbach_open_state

    def _cc_close(self) -> None:
        """Close FDX connection, UDP socket and shut down Trace32 App."""

        self.t32_api.T32_Stop()

        # Close FDX receiver communication
        fdxin_state = self.t32_api.T32_Fdx_Close(self.fdxin)
        log.internal_debug(
            f"Disconnected from FDX {self.fdxin} with state {fdxin_state}"
        )

        # Close FDX sender communication
        fdxout_state = self.t32_api.T32_Fdx_Close(self.fdxout)
        log.internal_debug(
            f"Disconnected from FDX {self.fdxout} with state {fdxout_state}"
        )

        # Reset Target
        reset_cpu_state = self.t32_api.T32_ResetCPU()
        log.internal_debug(f"Reset the CPU with state {reset_cpu_state}")

        # Reset the target if script provided
        if self.t32_reset_script_path is not None:
            self.load_script(self.t32_reset_script_path)

        # Close Trace32 application
        self.t32_api.T32_Cmd("QUIT".encode("latin-1"))

    def _cc_send(self, msg: bytes) -> int:
        """Sends a message using FDX channel.

        :param msg: message

        :return: poll length
        """
        log.internal_debug(f"===> {msg}")
        log.internal_debug(f"Sent on channel {self.fdxout}")

        # Create and fill the buffer with the message
        buffer = ctypes.pointer(ctypes.create_string_buffer(len(msg)))
        buffer.contents.raw = msg

        # Send the message
        poll_len = self.t32_api.T32_Fdx_SendPoll(self.fdxout, buffer, 1, len(msg))
        if poll_len <= 0:
            log.exception(
                f"ERROR occurred while sending {len(msg)} bytes on {self.fdxout}"
            )
        return poll_len

    def _cc_receive(self, timeout: float = 0.1) -> Dict[str, Union[bytes, str, None]]:
        """Receive message using the FDX channel.

        :return: message
        """
        # Add a small delay to allow other functions to execute
        time.sleep(0.1)

        received_msg = None
        if self.reset_flag:
            # If the Reset function is called, do not attempt to read messages
            return {"msg": received_msg}

        self.safe_reset_flag = False

        # Get the current time to process the timeout
        t_start = time.perf_counter()
        # Ensure to enter into the while loop (at least one time) if timeout is set to 0
        is_timeout = False
        # Check if a message has been received within the timeout
        while not is_timeout:
            # Create the buffer
            buffer = ctypes.pointer(
                ctypes.create_string_buffer(4096)
            )  # MaxSize = [0 ; 4096]

            # Check if msg available
            poll_len = self.t32_api.T32_Fdx_ReceivePoll(
                self.fdxin,
                buffer,
                len(buffer.contents[0]),
                int(len(buffer.contents) / len(buffer.contents[0])),
            )

            # Check if T32 api got an error
            if poll_len < 0:
                log.error(
                    f"ERROR occurred while listening channel {self.fdxin} with buffer: {buffer.contents.value}"
                )
                break

            # Check if a message has been received
            elif poll_len > 0:
                log.internal_info(f"Message size: {poll_len}")
                log.internal_info(
                    f"<=== {Message.parse_packet(buffer.contents.raw[:poll_len])}"
                )
                log.internal_debug(f"Received on channel {self.fdxin}")
                received_msg = Message.parse_packet(buffer.contents.raw[:poll_len])
                break

            # Exit the while loop once timeout is reached
            if time.perf_counter() > (t_start + timeout):
                is_timeout = True

        self.safe_reset_flag = True
        # No message received
        return {"msg": received_msg}

    def start(self) -> None:
        """Override clicking on "go" in the Trace32 application.

        The channel must have been successfully opened (Trace32
        application opened and script loaded).
        """
        self.t32_api.T32_Go()

    def reset_board(self) -> None:
        """Executes the board reset."""

        log.internal_debug(f"In Reset Function safety flag is: {self.safe_reset_flag}")
        log.internal_debug(f"In Reset Function reset flag is: {self.reset_flag}")

        while not self.safe_reset_flag:
            log.internal_debug(f"Safety flag in while loop is: {self.safe_reset_flag}")
            time.sleep(0.3)

        self.reset_flag = True
        log.internal_debug("Do the board reset")

        self.t32_api.T32_Stop()

        # Close FDX receiver communication
        fdxin_state = self.t32_api.T32_Fdx_Close(self.fdxin)
        log.internal_debug(
            f"Disconnected from FDX {self.fdxin} with state {fdxin_state}"
        )

        # Close FDX sender communication
        fdxout_state = self.t32_api.T32_Fdx_Close(self.fdxout)
        log.internal_debug(
            f"Disconnected from FDX {self.fdxout} with state {fdxout_state}"
        )

        # Reset Target
        reset_cpu_state = self.t32_api.T32_ResetCPU()
        log.internal_debug(f"Reset the CPU with state {reset_cpu_state}")

        # Run reset script
        if self.t32_in_test_reset_script_path is not None:
            self.load_script(self.t32_in_test_reset_script_path)

        # Get FDX receiver channel
        self.fdxin = self.t32_api.T32_Fdx_Open(b"FdxTestSendBuffer", b"r")
        if self.fdxin == -1:
            log.fatal("No FDXin buffer")

        # Get FDX sender channel
        self.fdxout = self.t32_api.T32_Fdx_Open(b"FdxTestReceiveBuffer", b"w")
        if self.fdxout == -1:
            log.fatal("No FDXout buffer")

        self.t32_api.T32_Go()
        self.reset_flag = False
        log.internal_debug("Reset finished")
