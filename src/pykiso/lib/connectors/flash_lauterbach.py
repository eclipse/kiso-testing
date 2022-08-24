##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Lauterbach Flasher
******************

:module: flash_lauterbach

:synopsis: used to flash through lauterbach probe.

.. currentmodule:: flash_lauterbach

.. warning: Still under test
"""
import ctypes
import enum
import logging
import subprocess
import time

from pykiso import connector

log = logging.getLogger(__name__)


class ScriptState(enum.IntEnum):
    """Use to determine script command execution."""

    UNKWON = -1
    NOT_RUNNING = 0
    RUNNING = 1
    DIALOG_OPEN = 2


class MessageLineState(enum.IntEnum):
    """Use to determine Message reading command."""

    ERROR = 2
    ERROR_INFO = 16


class LauterbachFlasher(connector.Flasher):
    """Connector used to flash through one and only one
    Lauterbach probe using Trace32 as remote API.
    """

    def __init__(
        self,
        t32_exc_path: str = None,
        t32_config: str = None,
        t32_script_path: str = None,
        t32_api_path: str = None,
        port: str = None,
        node: str = "localhost",
        packlen: str = "1024",
        device: int = 1,
        **kwargs,
    ):
        """Initialize attributes with configuration data.

        :param t32_exc_path: full path of Trace32 app to execute
        :param t32_config: full path of Trace32 configuration file
        :param t32_script_path: full path to .cmm flash script to execute
        :param t32_api_path: full path of remote api
        :param port: port number used for UDP communication
        :param node: node name (default localhost)
        :param packlen: data pack length for UDP communication (default 1024)
        :param device: configure device number given by Trace32 (default 1)
        """
        self.t32_script_path = t32_script_path
        self.t32_api_path = t32_api_path
        self.t32_start_args = [t32_exc_path, "-c", t32_config]
        self.port = str(port)
        self.node = str(node)
        self.packlen = str(packlen)
        self.device = device
        self.t32_process = None
        self.t32_api = None
        self.loadup_wait_time = 5
        self.allowed_t32_errors = 10
        super().__init__(self.t32_script_path, **kwargs)

    def open(self) -> None:
        """Open UDP socket between ITF and Trace32 loaded app.

        The open command leads to the following sub-tasks execution:

            - Open a Trace32 app
            - Load remote API using ctypes
            - Configure UPD channel (Port/buffer size...)
            - Open UDP connection
            - Make a ping request
        """
        # load Trace32 remote api
        try:
            self.t32_api = ctypes.cdll.LoadLibrary(self.t32_api_path)
            log.internal_info("Trace32 remote API loaded")
        except Exception as e:
            log.exception("Unable to open Trace32")
            raise e
        # Looking for an active Trace32 process and close it
        if self.t32_api.T32_Init() == 0:
            # Quit properly the previous T32 instance
            cmd_status = self.t32_api.T32_Cmd("QUIT".encode("latin-1"))
            log.internal_debug(
                f"Previous process Trace32 closed with exit code:{cmd_status}"
            )
            # Properly exit t32 api. Otherwise subsequential commands will fail
            self.t32_api.T32_Exit()

        # open a new Trace32 process
        try:
            self.t32_process = subprocess.Popen(self.t32_start_args)
            log.internal_debug(
                f"Trace32 process open with arguments {self.t32_start_args}"
            )
        except Exception as e:
            log.exception("Unable to open Trace32")
            raise e

        # wait until Trace32 app is launched
        time.sleep(self.loadup_wait_time)

        # channel configuration
        self.t32_api.T32_Config(b"NODE=", self.node.encode("utf-8"))
        self.t32_api.T32_Config(b"PORT=", self.port.encode("utf-8"))
        self.t32_api.T32_Config(b"PACKLEN=", self.packlen.encode("utf-8"))

        # open UDP connection with Trace32
        if self.t32_api.T32_Init() == 0:
            self.t32_api.T32_Attach(self.device)
            log.internal_info(f"ITF connected on {self.node}:{self.port}")
        else:
            log.fatal(f"Unable to connect on port : {self.port}")
            raise Exception(f"Unable to connect on port : {self.port}")

    def flash(self) -> None:
        """Flash software using configured .cmm script.

        The Flash command leads to the following sub-tasks execution :
            - Send to Trace32 CD.DO internal command (execute script)
            - Wait until script is finished
            - Get script execution verdict

        :raise Exception: if Trace32 error occurred during flash.
        """

        # read actual flash script content for logging puprpose
        with open(file=self.t32_script_path, mode="r") as script:
            log.internal_debug(
                f"flash using script at {self.t32_script_path}, with the following commands : {script.read()}"
            )

        # run flash script
        cmd = f"CD.DO {self.t32_script_path}"
        log.internal_info(f"Call T32_Cmd {cmd}")
        request_state = self.t32_api.T32_Cmd(cmd.encode("utf-8"))

        if request_state < 0:
            log.fatal("TRACE32 Remote API communication error")
            raise Exception("TRACE32 Remote API communication error")
        else:
            # wait until script's end
            script_state = ctypes.c_int(ScriptState.UNKWON)
            request_state = 0
            error_count = 0
            while not script_state.value == ScriptState.NOT_RUNNING:
                request_state = self.t32_api.T32_GetPracticeState(
                    ctypes.byref(script_state)
                )
                log.internal_debug(
                    f"Called T32_GetPracticeState. request_state: {request_state} "
                    f"script_state: {script_state.value} request error: {error_count}"
                )
                if request_state != 0:
                    error_count += 1
                if error_count >= self.allowed_t32_errors:
                    raise RuntimeError(
                        f"Error during lauterbach script run. Script: {self.t32_script_path}\n"
                        f"Abort execution because lauterbach was unresponsive for {error_count} times"
                    )
                time.sleep(1)

        # reset target
        cmd = "SYStem.RESet"
        log.internal_info(f"Call T32_Cmd {cmd}")
        request_state = self.t32_api.T32_Cmd(cmd.encode("utf-8"))

        # get script execution verdict
        script_state = ctypes.c_uint16(-1)
        message = ctypes.create_string_buffer(256)
        request_state = self.t32_api.T32_GetMessage(
            ctypes.byref(message), ctypes.byref(script_state)
        )

        msg = message.value.decode("utf-8")
        if (
            request_state == 0
            and not script_state.value == MessageLineState.ERROR
            and not script_state.value == MessageLineState.ERROR_INFO
        ):
            log.internal_info("flash procedure successful")
        else:
            log.fatal(
                f"An error occurred during flash,state : {script_state.value} -> {msg}"
            )
            raise Exception(
                f"An error occurred during flash,state : {script_state.value} -> {msg}"
            )

    def close(self) -> None:
        """Close UDP socket and shut down Trace32 App."""
        # Close Trace32 application
        self.t32_api.T32_Cmd("QUIT".encode("latin-1"))

        # close communication with Trace32
        exit_state = self.t32_api.T32_Exit()
        log.internal_info(f"Disconnect from Trace32 with state {exit_state}")

        # Process has to quit properly.
        # Otherwise lauterbach needs a power reset to rerun t32mppc.
        try:
            self.t32_process.wait(timeout=5)
        except Exception:
            log.internal_warning("Trace32 failed to exit properly")
