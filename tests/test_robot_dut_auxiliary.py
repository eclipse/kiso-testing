##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.dut_auxiliary import DutAux, DUTAuxiliary
from pykiso.message import MessageReportType, MessageType


@pytest.fixture
def dut_aux_instance(mocker):
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run", return_value=None
    )
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"itf_com_aux": DutAux("channel")},
    )
    return DUTAuxiliary()


class MockReportMsg:
    def __init__(self, report_type, message_type):
        self.sub_type = report_type
        self.message_type = message_type

    def get_message_type(self):
        return self.message_type


def test_run_ok(mocker, dut_aux_instance):

    mocked_report = MockReportMsg(MessageReportType.TEST_PASS, MessageType.REPORT)

    mock_report_infos = [(None, mocked_report, lambda *args: None, "Test OK")]

    mock_client = mocker.patch(
        "pykiso.lib.robot_framework.dut_auxiliary.handle_basic_interaction"
    )
    mock_client.return_value.__enter__.return_value = mock_report_infos

    dut_aux_instance.test_app_run(
        "TEST_CASE_RUN", 1, 1, ["itf_com_aux"], timeout_cmd=0, timeout_resp=0
    )


def test_run_failed(mocker, dut_aux_instance):

    mocked_report = MockReportMsg(MessageReportType.TEST_FAILED, MessageType.REPORT)

    mock_report_infos = [
        (None, mocked_report, lambda *args: None, "Something went wrong")
    ]

    mock_client = mocker.patch(
        "pykiso.lib.robot_framework.dut_auxiliary.handle_basic_interaction"
    )
    mock_client.return_value.__enter__.return_value = mock_report_infos

    with pytest.raises(AssertionError) as excinfo:
        dut_aux_instance.test_app_run(
            "TEST_CASE_RUN", 1, 1, ["itf_com_aux"], timeout_cmd=0, timeout_resp=0
        )
    assert "Something went wrong" in str(excinfo.value)


def test_run_not_implemented(mocker, dut_aux_instance):

    mocked_report = MockReportMsg(
        MessageReportType.TEST_NOT_IMPLEMENTED, MessageType.REPORT
    )

    mock_report_infos = [(None, mocked_report, lambda *args: None, "Not implemented")]
    mock_client = mocker.patch(
        "pykiso.lib.robot_framework.dut_auxiliary.handle_basic_interaction"
    )
    mock_client.return_value.__enter__.return_value = mock_report_infos

    with pytest.raises(AssertionError) as excinfo:
        dut_aux_instance.test_app_run(
            "TEST_CASE_RUN", 1, 1, ["itf_com_aux"], timeout_cmd=0, timeout_resp=0
        )
    assert "Not implemented" in str(excinfo.value)
