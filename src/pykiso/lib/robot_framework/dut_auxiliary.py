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

from typing import Any, Callable, List, Tuple

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

    def __init__(self) -> None:
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

    def _get_test_class_info(self, cmd_alias: str) -> Tuple[Any, Callable]:
        """Retrieve the corresponding couple test class/ test fixture
        based on the given command name.

        :param cmd_alias: command name or alias (TEST_CASE_RUN,
            TEST_CASE_SETUP...)

        :return: test class object to insatnciate and fixture name to
            call

        :raises TypeError: if the given command type doesn't exist
        """
        try:
            command = COMMAND_TYPE[cmd_alias]
        except KeyError:
            raise TypeError(f"unknown command type {cmd_alias}")

        return self.test_entity_mapping.get(command)

    @keyword(name="Test App")
    def test_app_run(
        self,
        command_type: str,
        test_suite_id: int,
        test_case_id: int,
        aux_list: List[str],
    ) -> None:
        """Execute the corresponding test fixture using Test App
        communication protocol.

        :param command_type: message command sub-type
        :param test_suite_id: select test suite id on dut
        :param test_case_id: select test case id on dut
        :param aux_list: List of selected auxiliary

        :raises TypeError: if the given command type doesn't exist
        :raises Assertion: if an aknowledgment is not received or the
            report status is failed.
        """

        auxiliaries = [self._get_aux(aux) for aux in aux_list]

        test_cls, fixture_alias = self._get_test_class_info(command_type)

        test_instance = test_cls(
            test_suite_id,
            test_case_id,
            auxiliaries,
            setup_timeout=None,
            run_timeout=None,
            teardown_timeout=None,
            test_ids=None,
            tag=None,
        )

        fixture_func = getattr(test_instance, fixture_alias)

        fixture_func()
