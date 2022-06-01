##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

from pykiso import message
from pykiso.lib.auxiliaries.example_test_auxiliary import ExampleAuxiliary


def test_abort_command(mocker, caplog):
    mocker_send_and_wait_ack = mocker.patch.object(
        ExampleAuxiliary, "_send_and_wait_ack"
    )
    mocker_send_and_wait_ack.return_value = False
    mocker.patch.object(message, "Message")
    mocker_delete_aux_instance = mocker.patch.object(
        ExampleAuxiliary, "_delete_auxiliary_instance"
    )
    mocker_create_aux_instance = mocker.patch.object(
        ExampleAuxiliary, "_create_auxiliary_instance"
    )
    with caplog.at_level(logging.INFO):
        result_abort = ExampleAuxiliary()._abort_command()

    mocker_create_aux_instance.assert_called()
    mocker_delete_aux_instance.assert_called()
    mocker_send_and_wait_ack.assert_called()
    assert result_abort is False
    assert "Send abort request" in caplog.text


def test__send_and_wait_ack_failed(mocker, mock_msg, cchannel_inst, caplog):
    mocker_check_if_ack_message_is_matching = mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching"
    )
    cchannel_inst._cc_receive.return_value = {"msg": "Message"}
    mocker_check_if_ack_message_is_matching.return_value = False

    with caplog.at_level(logging.WARNING):
        ExampleAuxiliary(com=cchannel_inst)._send_and_wait_ack(mock_msg, 0.5, 2)

    assert mocker_check_if_ack_message_is_matching.call_count == 2
    mocker_check_if_ack_message_is_matching.assert_called_with("Message")

    assert f"Received Message not matching {mock_msg}!" in caplog.text
