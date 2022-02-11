##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Simulation
**********

:module: simulation

:synopsis: map virtual DUT behavior with test case/suite id

.. currentmodule:: simulation

.. warning:: Still under test
"""
from collections import defaultdict

from .response_templates import ResponseTemplates
from .scenario import Scenario, TestScenario


class Simulation:
    """Simulate a virtual DUT, by playing pre-defined scenario depending on
    test case and test suite id.
    """

    def __init__(self):
        """Initialize attributes and mapping."""

        self.map_context = defaultdict(lambda: self.handle_default_response)
        self.map_context[0, 0] = self.handle_ping_pong
        self.map_context[1, 1] = TestScenario.handle_successful

        # test case setup mapping
        setup_tc = TestScenario.VirtualTestCase.Setup
        self.map_context[1, 2] = setup_tc.handle_failed_report_setup
        self.map_context[1, 3] = setup_tc.handle_not_implemented_report_setup
        self.map_context[1, 4] = setup_tc.handle_lost_communication_during_setup_ack
        self.map_context[1, 5] = setup_tc.handle_lost_communication_during_setup_report

        # test case run mapping
        run_tc = TestScenario.VirtualTestCase.Run
        self.map_context[1, 6] = run_tc.handle_failed_report_run
        self.map_context[1, 7] = run_tc.handle_not_implemented_report_run
        self.map_context[1, 8] = run_tc.handle_lost_communication_during_run_ack
        self.map_context[1, 9] = run_tc.handle_lost_communication_during_run_report
        self.map_context[1, 14] = TestScenario.handle_successful
        self.map_context[1, 15] = run_tc.handle_successful_report_run_with_log
        self.map_context[1, 16] = run_tc.handle_failed_report_run_with_log

        # test case teardown mapping
        td_tc = TestScenario.VirtualTestCase.Teardown
        self.map_context[1, 10] = td_tc.handle_failed_report_teardown
        self.map_context[1, 11] = td_tc.handle_not_implemented_report_teardown
        self.map_context[1, 12] = td_tc.handle_lost_communication_during_teardown_ack
        self.map_context[1, 13] = td_tc.handle_lost_communication_during_teardown_report

        # test suite setup mapping
        setup_ts = TestScenario.VirtualTestSuite.Setup
        self.map_context[2, 0] = setup_ts.handle_failed_report_setup
        self.map_context[3, 0] = setup_ts.handle_not_implemented_report_setup
        self.map_context[4, 0] = setup_ts.handle_lost_communication_during_setup_ack
        self.map_context[5, 0] = setup_ts.handle_lost_communication_during_setup_report

        # test suite teardown mapping
        td_ts = TestScenario.VirtualTestSuite.Teardown
        self.map_context[6, 0] = td_ts.handle_failed_report_teardown
        self.map_context[7, 0] = td_ts.handle_not_implemented_report_teardown
        self.map_context[8, 0] = td_ts.handle_lost_communication_during_teardown_ack
        self.map_context[9, 0] = td_ts.handle_lost_communication_during_teardown_report

    def get_scenario(self, test_suite_id: int, test_case_id: int) -> Scenario:
        """Return the selected scenario mapped with the received
        test case and test suite id.

        :param test_suite_id: current test suite id
        :param test_case_id: current test case id

        :return: scenario instance containing all steps
        """
        scenario = self.map_context[test_suite_id, test_case_id]()
        return scenario

    def handle_ping_pong(self) -> Scenario:
        """Return a scenario to handle init ping pong exchange.

        :return: scenario instance containing all steps
        """
        return Scenario([ResponseTemplates.ack])

    def handle_default_response(self) -> Scenario:
        """Return a scenario to handle DUT default behavior.

        :return: scenario instance containing all steps
        """
        return Scenario([ResponseTemplates.default])
