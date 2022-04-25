##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

from pykiso.lib.auxiliaries.simulated_auxiliary.scenario import (
    Scenario,
    TestScenario,
    ResponseTemplates,
)
import pytest


@pytest.fixture
def scenario_inst(mocker):
    mocker.patch.object(ResponseTemplates, "ack_with_report_ok", False)
    mocker.patch.object(ResponseTemplates, "ack", True)
    mocker.patch.object(ResponseTemplates, "ack_with_report_nok", "Test_nok")
    mocker.patch.object(
        ResponseTemplates,
        "ack_with_report_not_implemented",
        "Test_report_not_implemented",
    )
    mocker.patch.object(
        ResponseTemplates, "ack_with_logs_and_report_ok", "logs_and_reports"
    )
    mocker.patch.object(
        ResponseTemplates, "ack_with_logs_and_report_nok", "Test_report_nok_and_logs"
    )


def test_handle_successful(scenario_inst):
    result = TestScenario.handle_successful()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, False, False]


def test_handle_communication_lost(scenario_inst):
    result = TestScenario.handle_communication_lost()

    assert isinstance(result, Scenario)
    assert result == [True]


def test_virtualtestcase_setup_handle_failed_report_setup(scenario_inst):
    result = TestScenario.VirtualTestCase.Setup.handle_failed_report_setup()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == ["Test_nok", False, False]


def test_virtualtestcase_handle_not_implemented_report_setup(scenario_inst):
    result = TestScenario.VirtualTestCase.Setup.handle_not_implemented_report_setup()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == ["Test_report_not_implemented", False, False]


def test_virtualtestcase_setup_handle_lost_com_during_setup_ack(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Setup.handle_lost_communication_during_setup_ack()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [None, None, True, False, False]


def test_virtualtestcase_setup_handle_lost_communication_during_setup_report(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Setup.handle_lost_communication_during_setup_report()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [True, None, None, False, False]


def test_virtualtestcase_run_handle_failed_report_run(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Run.handle_failed_report_run()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, "Test_nok", False]


def test_virtualtestcase_run_handle_successful_report_run_with_log(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Run.handle_successful_report_run_with_log()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, "logs_and_reports", False]


def test_virtualtestcase_handle_failed_report_run_with_log(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Run.handle_failed_report_run_with_log()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, "Test_report_nok_and_logs", False]


def test_virtualtestcase_run_handle_not_implemented_report_run(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Run.handle_not_implemented_report_run()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, "Test_report_not_implemented", False]


def test_virtualtestcase_run_handle_lost_communication_during_run_ack(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Run.handle_lost_communication_during_run_ack()

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [False, None, None, True, False]


def test_virtualtestcase_run_handle_lost_communication_during_run_report(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Run.handle_lost_communication_during_run_report()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [False, True, None, None, False]


def test_virtualtestcase_handle_failed_report_teardown(
    scenario_inst,
):
    result = TestScenario.VirtualTestCase.Teardown.handle_failed_report_teardown()

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, False, "Test_nok"]


def test_virtualtestcase_handle_not_implemented_report_teardown(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Teardown.handle_not_implemented_report_teardown()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [False, False, "Test_report_not_implemented"]


def test_virtualtestcase_handle_lost_communication_during_teardown_ack(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Teardown.handle_lost_communication_during_teardown_ack()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [False, False, None, None, True]


def test_virtualtestcase_handle_lost_communication_during_teardown_report(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestCase.Teardown.handle_lost_communication_during_teardown_report()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 5
    assert result == [False, False, True, None, None]


def test_virtualtestsuite_setup_handle_failed_report_setup(scenario_inst):
    result = TestScenario.VirtualTestSuite.Setup.handle_failed_report_setup()

    assert isinstance(result, Scenario)
    assert result == ["Test_nok"]


def test_virtualtestsuite_handle_not_implemented_report_setup(scenario_inst):
    result = TestScenario.VirtualTestSuite.Setup.handle_not_implemented_report_setup()

    assert isinstance(result, Scenario)
    assert result == ["Test_report_not_implemented"]


def test_virtualtestsuite_setup_handle_lost_com_during_setup_ack(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestSuite.Setup.handle_lost_communication_during_setup_ack()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [None, None, True]


def test_virtualtestsuite_setup_handle_lost_communication_during_setup_report(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestSuite.Setup.handle_lost_communication_during_setup_report()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [True, None, None]


def test_virtualtestsuite_handle_failed_report_teardown(
    scenario_inst,
):
    result = TestScenario.VirtualTestSuite.Teardown.handle_failed_report_teardown()

    assert isinstance(result, Scenario)
    assert result == ["Test_nok"]


def test_virtualtestsuite_handle_not_implemented_report_teardown(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestSuite.Teardown.handle_not_implemented_report_teardown()
    )

    assert isinstance(result, Scenario)
    assert result == ["Test_report_not_implemented"]


def test_virtualtestsuite_handle_lost_communication_during_teardown_ack(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestSuite.Teardown.handle_lost_communication_during_teardown_ack()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [None, None, True]


def test_virtualtestsuite_handle_lost_communication_during_teardown_report(
    scenario_inst,
):
    result = (
        TestScenario.VirtualTestSuite.Teardown.handle_lost_communication_during_teardown_report()
    )

    assert isinstance(result, Scenario)
    assert len(result) == 3
    assert result == [True, None, None]
