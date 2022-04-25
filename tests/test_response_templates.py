##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest
from pykiso import message
from pykiso.lib.auxiliaries.simulated_auxiliary import response_templates

ACK = message.MessageType.ACK
ABORT = message.MessageCommandType.ABORT
PING = message.MessageCommandType.PING
TEST_SECTION_SETUP = message.MessageCommandType.TEST_SECTION_SETUP


@pytest.mark.parametrize(
    "msg_sub_type, function_to_mock, mock_return_value",
    [
        (TEST_SECTION_SETUP, "ack_with_report_ok", "Test_ack_report"),
        (PING, "ack", "test_ack"),
    ],
)
def test_default_valid(
    mocker, mock_msg, msg_sub_type, function_to_mock, mock_return_value
):
    mock_msg.sub_type = msg_sub_type
    mock_alc_report = mocker.patch.object(
        response_templates.ResponseTemplates,
        function_to_mock,
        return_value=mock_return_value,
    )

    result_default = response_templates.ResponseTemplates.default(mock_msg)
    mock_alc_report.assert_called()
    assert result_default == mock_return_value


def test_ack(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )

    result = response_templates.ResponseTemplates.ack(mock_msg)
    mock_generate_ack.assert_called()
    assert len(result) == 1
    assert isinstance(result[0], message.Message)


def test_ack_with_report_ok(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )

    result = response_templates.ResponseTemplates.ack_with_report_ok(mock_msg)
    mock_generate_ack.assert_called()
    assert len(result) == 2
    assert all(isinstance(items, message.Message) for items in result)


def test_ack_with_report_nok(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )
    mock_random = mocker.patch.object(
        response_templates.ResponseTemplates, "get_random_reason", return_value=dict()
    )
    result = response_templates.ResponseTemplates.ack_with_report_nok(mock_msg)
    mock_random.assert_called()
    mock_generate_ack.assert_called()
    assert len(result) == 2
    assert all(isinstance(items, message.Message) for items in result)


def test_get_random_reason():
    result_get_random = response_templates.ResponseTemplates.get_random_reason()
    assert isinstance(result_get_random, dict)
    assert len(result_get_random)
    assert (
        result_get_random.get(message.TlvKnownTags.FAILURE_REASON)
        in response_templates.ResponseTemplates.reasons_list
    )


def test_ack_with_logs_and_report_ok(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )
    result = response_templates.ResponseTemplates.ack_with_logs_and_report_ok(mock_msg)
    mock_generate_ack.assert_called()
    assert len(result) == 4
    assert all(isinstance(items, message.Message) for items in result)


def test_ack_with_logs_and_report_nok(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )
    mocker.patch.object(
        response_templates.ResponseTemplates, "get_random_reason", return_value=dict()
    )
    result = response_templates.ResponseTemplates.ack_with_logs_and_report_nok(mock_msg)
    mock_generate_ack.assert_called()

    assert len(result) == 4
    assert all(isinstance(items, message.Message) for items in result)
    assert isinstance(result[3].tlv_dict, dict)


def test_nack_with_reason(mocker, mock_msg):
    mock_generate_ack = mocker.patch.object(
        message.Message,
        "generate_ack_message",
        return_value=message.Message(tlv_dict=dict()),
    )
    mock_random = mocker.patch.object(
        response_templates.ResponseTemplates,
        "get_random_reason",
        return_value={"Test": "random"},
    )

    result = response_templates.ResponseTemplates.nack_with_reason(mock_msg)
    mock_generate_ack.assert_called()
    mock_random.assert_called()
    assert len(result) == 1
    assert isinstance(result[0], message.Message)
    assert result[0].tlv_dict.get("Test") == "random"


def test_ack_with_report_not_implemented(mocker, mock_msg):

    mock_generate_ack = mocker.patch.object(
        message.Message, "generate_ack_message", return_value=message.Message()
    )

    result = response_templates.ResponseTemplates.ack_with_report_not_implemented(
        mock_msg
    )
    mock_generate_ack.assert_called()
    assert len(result) == 2
    assert all(isinstance(items, message.Message) for items in result)
