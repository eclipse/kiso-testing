##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.dut_auxiliary import (
    COMMAND_TYPE,
    DutAux,
    DUTAuxiliary,
    RemoteTest,
    RemoteTestSuiteSetup,
    RemoteTestSuiteTeardown,
)
from pykiso.message import Message, MessageReportType, MessageType

RemoteTest.__test__ = False
RemoteTestSuiteSetup.__test__ = False
RemoteTestSuiteTeardown.__test__ = False


@pytest.fixture
def mock_dut_aux(mocker, cchannel_inst):
    class MockDutAux(DutAux):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        send_ping_command = mocker.stub(name="send_ping_command")
        send_fixture_command = mocker.stub(name="send_fixture_command")
        send_abort_command = mocker.stub(name="send_abort_command")
        wait_and_get_report = mocker.stub(name="send_abort_command")

    return MockDutAux


@pytest.fixture
def aux_instance(mocker, mock_dut_aux, cchannel_inst):

    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"itf_com_aux": mock_dut_aux(com=cchannel_inst)},
    )
    return DUTAuxiliary()


@pytest.mark.parametrize(
    "command, test_cls, fixture_alias",
    [
        ("TEST_SUITE_SETUP", RemoteTestSuiteSetup, "test_suite_setUp"),
        ("TEST_SUITE_TEARDOWN", RemoteTestSuiteTeardown, "test_suite_tearDown"),
        ("TEST_CASE_SETUP", RemoteTest, "setUp"),
        ("TEST_CASE_RUN", RemoteTest, "test_run"),
        ("TEST_CASE_TEARDOWN", RemoteTest, "tearDown"),
    ],
)
def test_get_test_class_info(aux_instance, command, test_cls, fixture_alias):

    info = aux_instance._get_test_class_info(command)

    assert info == (test_cls, fixture_alias)


def test_get_test_class_info_unknown_command(aux_instance):

    with pytest.raises(TypeError):
        aux_instance._get_test_class_info("feel like I am a nice command")


@pytest.mark.parametrize(
    "command",
    [
        ("TEST_SUITE_SETUP"),
        ("TEST_SUITE_TEARDOWN"),
        ("TEST_CASE_SETUP"),
        ("TEST_CASE_RUN"),
        ("TEST_CASE_TEARDOWN"),
    ],
)
def test_app_run(mocker, aux_instance, command):
    report = Message(
        msg_type=MessageType.REPORT,
        sub_type=MessageReportType.TEST_PASS,
        test_suite=1,
        test_case=1,
    )
    mock_dut = aux_instance._get_aux("itf_com_aux")
    mocker.patch.object(mock_dut, "send_fixture_command", return_value=True)
    mocker.patch.object(mock_dut, "wait_and_get_report", return_value=report)

    aux_instance.test_app_run(
        command, test_suite_id=1, test_case_id=1, aux_list=["itf_com_aux"]
    )

    mock_dut = aux_instance._get_aux("itf_com_aux")

    mock_dut.send_fixture_command.assert_called_once()
    mock_dut.wait_and_get_report.assert_called_once()


def test_app_run_report_failed(mocker, aux_instance):
    report = Message(
        msg_type=MessageType.REPORT,
        sub_type=MessageReportType.TEST_FAILED,
        test_suite=1,
        test_case=1,
    )
    mock_dut = aux_instance._get_aux("itf_com_aux")
    mocker.patch.object(mock_dut, "send_fixture_command", return_value=True)
    mocker.patch.object(mock_dut, "wait_and_get_report", return_value=report)

    with pytest.raises(AssertionError):
        aux_instance.test_app_run(
            "TEST_SUITE_SETUP",
            test_suite_id=1,
            test_case_id=1,
            aux_list=["itf_com_aux"],
        )


def test_app_run_not_ack(mocker, aux_instance):
    mock_dut = aux_instance._get_aux("itf_com_aux")
    mocker.patch.object(mock_dut, "send_fixture_command", return_value=False)

    with pytest.raises(AssertionError):
        aux_instance.test_app_run(
            "TEST_SUITE_SETUP",
            test_suite_id=1,
            test_case_id=1,
            aux_list=["itf_com_aux"],
        )
