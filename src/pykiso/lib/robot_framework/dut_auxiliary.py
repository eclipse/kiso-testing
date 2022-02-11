##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Testapp binding
***************

:module: dut_auxiliary

:synopsis: implementation of existing DUTAuxiliary for Robot
    framework usage.

.. currentmodule:: dut_auxiliary

"""

from typing import List

from robot.api import logger
from robot.api.deco import keyword, library

from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.message import MessageCommandType, MessageReportType, MessageType
from pykiso.test_coordinator.test_message_handler import (
    handle_basic_interaction,
)

from ..auxiliaries.dut_auxiliary import DUTAuxiliary as DutAux
from .aux_interface import RobotAuxInterface


class TestEntity:
    """Dummy Class to use handle_basic_interaction from test_message_handler."""

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: List[AuxiliaryInterface],
    ):
        """Initialize generic test-case

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used aux_list"""

        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id
        self.test_auxiliary_list = aux_list

    def cleanup_and_skip(self, aux: AuxiliaryInterface, info_to_print: str):
        """Cleanup auxiliary and log reasons.

        :param aux: corresponding auxiliary to abort
        :param info_to_print: A message you want to print while cleaning up the test
        """
        logger.error(info_to_print)

        # Send aborts to corresponding auxiliary
        if aux.abort_command() is not True:
            logger.error(f"Error occurred during abort command on auxiliary {aux}")


@library(version="0.0.1")
class DUTAuxiliary(RobotAuxInterface):
    """Robot library to control the TestApp on the DUT"""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=DutAux)

    @keyword(name="Test App")
    def test_app_run(
        self,
        command_type: str,
        test_suite_id: int,
        test_case_id: int,
        aux_list: List[str],
        timeout_cmd: int = 5,
        timeout_resp: int = 5,
    ) -> None:
        """Handle default communication mechanism between test manager and device under test.

        :param command_type: message command sub-type (TEST_SECTION_SETUP , TEST_SECTION_RUN, ...)
        :param test_suite_id: select test suite id on dut
        :param test_case_id: select test case id on dut
        :param aux_list: List of selected auxiliary
        :param timeout_cmd: timeout in seconds for auxiliary run_command
        :param timeout_resp: timeout in seconds for auxiliary wait_and_get_report
        """

        auxiliaries = [self._get_aux(aux) for aux in aux_list]

        test_entity = TestEntity(test_suite_id, test_case_id, auxiliaries)

        with handle_basic_interaction(
            test_entity,
            MessageCommandType[command_type],
            timeout_cmd,
            timeout_resp,
        ) as report_infos:

            for _, report_msg, log_level_func, log_msg in report_infos:
                log_level_func(log_msg)

                if report_msg.get_message_type() == MessageType.REPORT:

                    if not report_msg.sub_type == MessageReportType.TEST_PASS:
                        # Raise assertion to make test red in robotframework
                        raise AssertionError(f"Test Failed:{log_msg}")
