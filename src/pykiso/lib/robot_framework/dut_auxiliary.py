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

from pykiso.test_coordinator.test_case import RemoteTest
from pykiso.test_coordinator.test_suite import (
    RemoteTestSuiteSetup,
    RemoteTestSuiteTeardown,
)

from ..auxiliaries.dut_auxiliary import COMMAND_TYPE
from ..auxiliaries.dut_auxiliary import DUTAuxiliary as DutAux
from .aux_interface import RobotAuxInterface


@library(version="0.0.1")
class DUTAuxiliary(RobotAuxInterface):
    """Robot library to control the TestApp on the DUT"""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=DutAux)
        self.test_entity_mapping = {
            COMMAND_TYPE.TEST_SUITE_SETUP: (RemoteTestSuiteSetup, "test_suite_setUp"),
            COMMAND_TYPE.TEST_SUITE_TEARDOWN: (
                RemoteTestSuiteTeardown,
                "test_suite_tearDown",
            ),
            COMMAND_TYPE.TEST_CASE_SETUP: (RemoteTest, "setUp"),
            COMMAND_TYPE.TEST_CASE_RUN: (RemoteTest, "test_run"),
            COMMAND_TYPE.TEST_CASE_TEARDOWN: (RemoteTest, "tearDown"),
        }

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

        test_cls, fixture_alias = self.test_entity_mapping.get(
            COMMAND_TYPE[command_type]
        )

        if test_cls is None:
            raise TypeError(f"unknown command type {command_type}")

        test_instance = test_cls(
            test_suite_id,
            test_case_id,
            auxiliaries,
            setup_timeout=None,
            run_timeout=None,
            teardown_timeout=None,
            test_ids=None,
            tag=None,
            args=(),
            kwargs={},
        )

        fixture_func = getattr(test_instance, fixture_alias)

        fixture_func()
