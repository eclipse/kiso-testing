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
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from pykiso import SimpleAuxiliaryInterface
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


class Twister:
    """Control class for the Zephyr twister commandline tool"""

    def __init__(self, twister_path: str = "twister") -> None:
        self.twister_path = twister_path
        self.process: Optional[subprocess.Popen[bytes]] = None

    def start_test(
        self, test_directory: str, testcase_name: str, wait_for_start: bool = True
    ) -> None:
        """Start the test case

        :param test_directory: The directory to search for the Zephyr test project (passed to twister using the -T parameter)
        :param testcase_name: The name of the Zephyr test (passed to twister using the -s parameter)
        :param wait_for_start: Wait for the test case to start on the target. If this is set to false the function will just return even if the test is not running yet.

        :return: True if successful
        """
        if self.process is not None:
            raise ZephyrError("Twister test is already running")

        self.outdir = str(Path(test_directory).resolve() / "twister-out")
        logging.info(f"Using Twister output directory: {self.outdir}")

        self.process = subprocess.Popen(
            [
                self.twister_path,
                "-vv",
                "-T",
                test_directory,
                "-s",
                testcase_name,
                "--outdir",
                self.outdir,
                "--report-dir",
                self.outdir,
            ],
            stderr=subprocess.PIPE,
            shell=False,
        )

        if wait_for_start:
            # Read twister output until test case was started
            while True:
                line = self._readline()
                if line == None:
                    return

                if "OUTPUT: START - " in line:
                    log.info(f"Zephyr test started.")
                    return

    def _readline(self) -> Optional[str]:
        """Read a line from the twister process

        :return: The line as string or None if the process has finished
        """
        while True:
            read = self.process.stderr.readline()
            if len(read) == 0:
                return None
            line = read.decode("utf-8").strip()
            # Twister outputs many lines without a real message, remove those
            test_output_pattern = "- OUTPUT:"
            output = line.find(test_output_pattern)
            if output != -1:
                message = line[output + len(test_output_pattern) :]
                if len(message) == 0 or message.isspace():
                    continue
            log.debug(f"Twister: {line}")
            return line

    def _parse_xunit(self, file_path: str) -> TestResult:
        """Parse xunit file

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
            log.info(f"Zephyr test was skipped.")
            result = TestResult.SKIPPED
        elif error is not None:
            log.error(f"Zephyr test failed with error: {error.text}")
            result = TestResult.ERROR
        else:
            log.info(f"Zephyr test PASSED.")
            result = TestResult.PASSED
        return result

    def wait_test(self) -> TestResult:
        """Wait for the test to finish

        :return: The result of the test, taken from the xunit output of twister
        """
        if self.process is None:
            raise ZephyrError("Twister was not started so can not wait.")

        # Read the twister console for log output
        while True:
            line = self._readline()
            if line is None:
                break

            # Look for relevant messages in the output
            if "OUTPUT:  PASS - " in line:
                log.debug(f"Zephyr test PASSED.")
            elif "OUTPUT:  FAIL - " in line:
                log.debug(f"Zephyr test FAILED.")

        # Wait for the twister process to exit
        ret = self.process.wait()

        # Get the result from the xunit file
        result = self._parse_xunit(str(Path(self.outdir) / "twister_report.xml"))

        self.process = None
        return result


class ZephyrTestAuxiliary(SimpleAuxiliaryInterface):
    """Auxiliary for Zephyr test interaction using the twister commandline tool

    The functionality includes test case execution and result collection.

    """

    def __init__(
        self,
        twister_path: str = "twister",
        test_directory: Optional[str] = None,
        test_name: Optional[str] = None,
        wait_for_start: bool = True,
        **kwargs,
    ) -> None:
        """Initialize the auxiliary

        :param twister_path: Path to the twister tool
        :param test_directory: The directory to search for the Zephyr test project
        :param testcase_name: The name of the Zephyr test
        :param wait_for_start: Wait for Zyephyr test start

        """
        self.twister_path = twister_path
        self.test_directory = test_directory
        self.test_name = test_name
        self.wait_for_start = wait_for_start
        self.twister = Twister(twister_path)
        super().__init__(**kwargs)

    def start_test(
        self, test_directory: Optional[str] = None, test_name: Optional[str] = None
    ) -> None:
        """Start the Zephyr test

        :param test_directory: The directory to search for the Zephyr test project. Defaults to the test_directory from YAML.
        :param testcase_name: The name of the Zephyr test. Defaults to the testcase_name from YAML.
        """
        test_directory = (
            test_directory if test_directory is not None else self.test_directory
        )
        test_name = test_name if test_name is not None else self.test_name
        if test_directory is None:
            raise ZephyrError("test_directory parameter is not set.")
        if test_name is None:
            raise ZephyrError("test_name parameter is not set.")
        self.twister.start_test(test_directory, test_name, self.wait_for_start)

    def wait_test(self) -> TestResult:
        return self.twister.wait_test()

    def _create_auxiliary_instance(self) -> bool:
        return True

    def _delete_auxiliary_instance(self) -> bool:
        return True
