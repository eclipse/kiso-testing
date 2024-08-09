##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import pytest

from pykiso.lib.auxiliaries.simulated_auxiliary import Simulation
from pykiso.lib.auxiliaries.simulated_auxiliary.scenario import ResponseTemplates, Scenario, TestScenario


class TestSimulation:

    simulation_instance = None
    simulation_another_instance = None

    @pytest.fixture
    def simulation_inst(self, mocker):
        mocker.patch.object(
            TestScenario,
            "handle_successful",
            Scenario(["handle_successful", False]),
        )
        mocker.patch.object(
            Simulation,
            "handle_ping_pong",
            Scenario(["handle_ping_pong", False]),
        )

        mocker.patch.object(
            TestScenario.VirtualTestCase.Setup,
            "handle_failed_report_setup",
            Scenario([True, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Setup,
            "handle_not_implemented_report_setup",
            Scenario(["Test_implemented", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Setup,
            "handle_lost_communication_during_setup_ack",
            Scenario([False, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Setup,
            "handle_lost_communication_during_setup_report",
            Scenario(["Test_report", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Setup,
            "handle_failed_report_setup",
            Scenario(["Test_suite_handle_fail_rep_setup", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Setup,
            "handle_not_implemented_report_setup",
            Scenario([None, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Setup,
            "handle_lost_communication_during_setup_ack",
            Scenario(["Test_suite_lost_com_during_ack", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Setup,
            "handle_lost_communication_during_setup_report",
            Scenario(["handle_lost_communication_during_setup_report", False]),
        )

        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_failed_report_run",
            Scenario(["Test_report_run_failed", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_not_implemented_report_run",
            Scenario(["Test_reprun_not_implemented", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_lost_communication_during_run_ack",
            Scenario(["Test_lost_com_during_run_ack", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_lost_communication_during_run_report",
            Scenario(["Test_lost_com_during_run_rep", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_successful_report_run_with_log",
            Scenario(["Test_lost_com_rep_log", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Run,
            "handle_failed_report_run_with_log",
            Scenario([None, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Teardown,
            "handle_failed_report_teardown",
            Scenario(["Test_report_Teardown", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Teardown,
            "handle_not_implemented_report_teardown",
            Scenario(["Test_notipml_report_teardown", True]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Teardown,
            "handle_lost_communication_during_teardown_ack",
            Scenario(["Test_lost_com_teardown", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestCase.Teardown,
            "handle_lost_communication_during_teardown_report",
            Scenario(["Test_lost_com_during_teardown_rep", False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Teardown,
            "handle_failed_report_teardown",
            Scenario([True, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Teardown,
            "handle_not_implemented_report_teardown",
            Scenario([False, True]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Teardown,
            "handle_lost_communication_during_teardown_ack",
            Scenario([None, False]),
        )
        mocker.patch.object(
            TestScenario.VirtualTestSuite.Teardown,
            "handle_lost_communication_during_teardown_report",
            return_value=Scenario([True, False]),
        )

        TestSimulation.simulation_instance = Simulation()

        return TestSimulation.simulation_instance

    @pytest.fixture
    def simulation_inst_handle(self, mocker):
        mocker.patch.object(ResponseTemplates, "ack", ["test_ack", None, True])

        TestSimulation.simulation_another_instance = Simulation()

        return TestSimulation.simulation_another_instance

    def test_constructor(self, simulation_inst):

        assert isinstance(simulation_inst.map_context[1, 6], Scenario)
        assert simulation_inst.map_context[0, 0].pop(0) == "handle_ping_pong"
        assert simulation_inst.map_context[1, 1].pop(0) == "handle_successful"
        assert simulation_inst.map_context[1, 2].pop(0) is True
        assert simulation_inst.map_context[1, 3].pop(0) == "Test_implemented"
        assert simulation_inst.map_context[1, 4].pop(0) is False
        assert simulation_inst.map_context[1, 5].pop(0) == "Test_report"
        assert simulation_inst.map_context[1, 6].pop(0) == "Test_report_run_failed"
        assert simulation_inst.map_context[1, 7].pop(0) == "Test_reprun_not_implemented"
        assert (
            simulation_inst.map_context[1, 8].pop(0) == "Test_lost_com_during_run_ack"
        )
        assert (
            simulation_inst.map_context[1, 9].pop(0) == "Test_lost_com_during_run_rep"
        )
        assert simulation_inst.map_context[1, 10].pop(0) == "Test_report_Teardown"
        assert (
            simulation_inst.map_context[1, 11].pop(0) == "Test_notipml_report_teardown"
        )
        assert simulation_inst.map_context[1, 12].pop(0) == "Test_lost_com_teardown"
        assert (
            simulation_inst.map_context[1, 13].pop(0)
            == "Test_lost_com_during_teardown_rep"
        )
        assert simulation_inst.map_context[1, 14].pop(0) is False
        assert simulation_inst.map_context[1, 15].pop(0) == "Test_lost_com_rep_log"
        assert simulation_inst.map_context[1, 16].pop(0) is None
        assert (
            simulation_inst.map_context[2, 0].pop(0)
            == "Test_suite_handle_fail_rep_setup"
        )
        assert simulation_inst.map_context[3, 0].pop(0) is None
        assert (
            simulation_inst.map_context[4, 0].pop(0) == "Test_suite_lost_com_during_ack"
        )
        assert (
            simulation_inst.map_context[5, 0].pop(0)
            == "handle_lost_communication_during_setup_report"
        )
        assert simulation_inst.map_context[6, 0].pop(0) is True
        assert simulation_inst.map_context[7, 0].pop(0) is False
        assert simulation_inst.map_context[8, 0].pop(0) is None

    def test_get_scenario(self, simulation_inst):
        result_get_scenario = simulation_inst.get_scenario(9, 0)
        assert isinstance(result_get_scenario, Scenario)
        assert result_get_scenario[0] is True
        assert result_get_scenario[1] is False

    def test_handle_ping_pong(self, simulation_inst_handle, mocker):
        result_handle_ping_pong = simulation_inst_handle.handle_ping_pong()

        assert isinstance(result_handle_ping_pong, Scenario)
        assert result_handle_ping_pong[0][0] == "test_ack"
        assert result_handle_ping_pong[0][1] is None
        assert result_handle_ping_pong[0][2] is True

    def test_handle_default_response(self, simulation_inst, mocker):
        mocker.patch.object(ResponseTemplates, "default", True)
        result_handle_default_response = simulation_inst.handle_default_response()

        assert isinstance(result_handle_default_response, Scenario)
        assert result_handle_default_response[0] is True
