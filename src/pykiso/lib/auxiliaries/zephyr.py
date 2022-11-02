##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import enum
import logging
import queue
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from pykiso import CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)
from pykiso.types import MsgType

log = logging.getLogger(__name__)


class TestResult(enum.IntEnum):
    """Result of a twister test"""

    PASSED = 0
    FAILED = 1
    SKIPPED = 2
    ERROR = 3


class ZephyrError(Exception):
    """Exception for twister errors"""

    pass


class ZephyrTestAuxiliary(DTAuxiliaryInterface):
    """Auxiliary for Zephyr test interaction using the twister commandline tool

    The functionality includes test case execution and result collection.

    """

    TEST_OUTPUT_PATTERN = "- OUTPUT:"
    TEST_PASS_PATTERN = "OUTPUT:  PASS - "
    TEST_START_PATTERN = "OUTPUT: START - "
    TEST_FAIL_PATTERN = "OUTPUT:  FAIL - "

    def __init__(
        self,
        com: CChannel = None,
        test_directory: Optional[str] = None,
        test_name: Optional[str] = None,
        wait_for_start: bool = True,
        **kwargs: dict,
    ) -> None:
        """Initialize the auxiliary

        :param test_directory: The directory to search for the Zephyr test project
        :param testcase_name: The name of the Zephyr test
        :param wait_for_start: Wait for Zyephyr test start

        """
        super().__init__(
            is_proxy_capable=True, tx_task_on=False, rx_task_on=False, **kwargs
        )
        self.test_directory = test_directory
        self.test_name = test_name
        self.wait_for_start = wait_for_start
        self.channel = com
        self.running = False

    def _run_command(self, cmd_message: str, cmd_data: bytes = None) -> bool:
        return True

    def _receive_message(self, timeout_in_s: float) -> None:
        pass

    def start_test(
        self, test_directory: Optional[str] = None, test_name: Optional[str] = None
    ) -> None:
        """Start the Zephyr test

        :param test_directory: The directory to search for the Zephyr test project. Defaults to the test_directory from YAML.
        :param testcase_name: The name of the Zephyr test. Defaults to the testcase_name from YAML.
        """
        test_directory = test_directory or self.test_directory
        test_name = test_name or self.test_name
        if test_directory is None:
            raise ZephyrError("test_directory parameter is not set.")
        if test_name is None:
            raise ZephyrError("test_name parameter is not set.")

        if self.running:
            raise ZephyrError("Twister test is already running")

        self.outdir = str(Path(test_directory).resolve() / "twister-out")
        log.internal_info(f"Using Twister output directory: {self.outdir}")
        self.channel.cc_send(
            {
                "command": "start",
                "args": [
                    "-vv",
                    "-T",
                    test_directory,
                    "-s",
                    test_name,
                    "--outdir",
                    self.outdir,
                    "--report-dir",
                    self.outdir,
                ],
            }
        )

        self.running = True
        if self.wait_for_start:
            # Read twister output until test case was started
            while True:
                line = self._readline()
                if line is None:
                    return

                if self.TEST_START_PATTERN in line:
                    log.internal_debug("Zephyr test started.")
                    return

    def _readline(self) -> Optional[str]:
        """Read a line from the twister process

        :return: The line as string or None if the process has finished
        """
        if not self.running:
            return None

        while True:
            msg = self.channel.cc_receive(timeout=None).get("msg")
            if msg is None:
                return None
            line = msg.get("stderr")
            if line is None:
                if "exit" in msg:
                    self.running = False
                    return None

            # Twister outputs many lines without a real message, remove those
            output = line.find(self.TEST_OUTPUT_PATTERN)
            if output != -1:
                message = line[output + len(self.TEST_OUTPUT_PATTERN) :]
                if not message.strip():
                    continue
            log.internal_debug(f"Twister: {line}")
            return line

    def wait_test(self) -> TestResult:
        """Wait for the test to finish

        :return: The result of the test, taken from the xunit output of twister
        """
        if not self.running:
            raise ZephyrError("Twister was not started so can not wait.")

        # Read the twister console for log output and wait for exit
        while True:
            line = self._readline()
            if line is None:
                break
            # Look for relevant messages in the output
            if self.TEST_PASS_PATTERN in line:
                log.internal_debug("Zephyr test PASSED.")
            elif self.TEST_FAIL_PATTERN in line:
                log.internal_debug("Zephyr test FAILED.")

        # Get the result from the xunit file
        result = self._parse_xunit(str(Path(self.outdir) / "twister_report.xml"))

        return result

    def _parse_xunit(self, file_path: str) -> TestResult:
        """Parse xunit file

        :param file_path: Path to the xunit file

        :return: The result of a single test case
        """
        tree = ET.parse(file_path)
        testcase = tree.getroot().find("testsuite").find("testcase")
        failure = testcase.find("failure")
        skipped = testcase.find("skipped")
        error = testcase.find("error")
        if failure is not None:
            log.info(f"Zephyr test failed: {failure.text}")
            result = TestResult.FAILED
        elif skipped is not None:
            log.info("Zephyr test was skipped.")
            result = TestResult.SKIPPED
        elif error is not None:
            log.error(f"Zephyr test failed with error: {error.text}")
            result = TestResult.ERROR
        else:
            log.info("Zephyr test PASSED.")
            result = TestResult.PASSED
        return result

    def _create_auxiliary_instance(self) -> bool:
        return True

    def _delete_auxiliary_instance(self) -> bool:
        return True
