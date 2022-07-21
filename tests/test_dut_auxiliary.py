##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import threading
from typing import Optional

import pytest

from pykiso.exceptions import AuxiliaryCreationError
from pykiso.lib.auxiliaries.dut_auxiliary import (
    COMMAND_TYPE,
    MESSAGE_TYPE,
    REPORT_TYPE,
    DUTAuxiliary,
    message,
    queue,
)


@pytest.fixture
def aux_inst(cchannel_inst, flasher_inst):
    return DUTAuxiliary(name="dut_aux", com=cchannel_inst, flash=flasher_inst)


def test_aux_constructor(aux_inst):
    aux_inst.tx_task_on is True
    aux_inst.rx_task_on is True
    aux_inst.is_proxy_capable is False
    aux_inst.current_cmd is None


def test_create_auxiliary_instance(aux_inst):
    state = aux_inst._create_auxiliary_instance()

    aux_inst.flash.open.assert_called_once()
    aux_inst.flash.flash.assert_called_once()
    aux_inst.flash.close.assert_called_once()
    aux_inst.channel._cc_open.assert_called_once()
    assert state is True


def test_create_auxiliary_instance_flasher_fail(mocker, aux_inst):
    mocker.patch.object(aux_inst.flash, "open", side_effect=AssertionError)
    state = aux_inst._create_auxiliary_instance()
    assert state is False


def test_create_auxiliary_instance_channel_fail(mocker, aux_inst):
    mocker.patch.object(aux_inst.channel, "_cc_open", side_effect=AssertionError)

    state = aux_inst._create_auxiliary_instance()

    assert state is False


def test_delete_auxiliary_instance(aux_inst):
    state = aux_inst._delete_auxiliary_instance()

    aux_inst.channel._cc_close.assert_called_once()
    assert state is True


def test_delete_auxiliary_instance_channel_fail(mocker, aux_inst):
    mocker.patch.object(aux_inst.channel, "_cc_close", side_effect=AssertionError)

    state = aux_inst._delete_auxiliary_instance()

    assert state is False


def test_create_instance(mocker, aux_inst):
    start_mock = mocker.patch.object(threading.Thread, "start")
    ping_mock = mocker.patch.object(aux_inst, "send_ping_command", return_value=True)

    state = aux_inst.create_instance()

    start_mock.assert_called()
    ping_mock.assert_called_once()
    assert state is True


def test_create_instance_fail(mocker, aux_inst):
    mocker.patch.object(aux_inst.flash, "open", side_effect=AssertionError)

    with pytest.raises(AuxiliaryCreationError):
        aux_inst.create_instance()


def test_send_ping_command(mocker, aux_inst):
    aux_inst.queue_out.put("something")
    match_mock = mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=True
    )
    run_mock = mocker.patch.object(aux_inst, "run_command", return_value=True)

    state = aux_inst.send_ping_command(timeout=10)

    match_mock.assert_called_once()
    run_mock.assert_called_once_with(
        cmd_message=aux_inst.current_cmd, cmd_data=None, blocking=True, timeout_in_s=10
    )
    assert aux_inst.current_cmd.msg_type == MESSAGE_TYPE.COMMAND
    assert aux_inst.current_cmd.sub_type == COMMAND_TYPE.PING
    assert state is True


def test_send_ping_command_no_ack(mocker, aux_inst):
    mocker.patch.object(aux_inst, "run_command", return_value=None)

    state = aux_inst.send_ping_command(timeout=10)

    assert state is False


def test_send_ping_command_failed_ack(mocker, aux_inst):
    mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=False
    )
    mocker.patch.object(aux_inst, "run_command", return_value=True)

    state = aux_inst.send_ping_command(timeout=10)

    assert state is False


def test_send_abord_command(mocker, aux_inst):
    match_mock = mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=True
    )
    run_mock = mocker.patch.object(aux_inst, "run_command", return_value=True)
    mock_create = mocker.patch.object(aux_inst, "create_instance")
    mock_delete = mocker.patch.object(aux_inst, "delete_instance")

    state = aux_inst.send_abort_command(timeout=5)

    match_mock.assert_called_once()
    mock_create.assert_not_called()
    mock_delete.assert_not_called()
    run_mock.assert_called_once_with(
        cmd_message=aux_inst.current_cmd, cmd_data=None, blocking=True, timeout_in_s=5
    )
    assert aux_inst.current_cmd.msg_type == MESSAGE_TYPE.COMMAND
    assert aux_inst.current_cmd.sub_type == COMMAND_TYPE.ABORT
    assert state is True


def test_send_abord_command_no_ack(mocker, aux_inst):
    mocker.patch.object(aux_inst, "run_command", return_value=None)
    mock_create = mocker.patch.object(aux_inst, "create_instance")
    mock_delete = mocker.patch.object(aux_inst, "delete_instance")

    state = aux_inst.send_abort_command(timeout=5)

    mock_create.assert_called()
    mock_delete.assert_called()
    assert state is False


def test_send_ping_command_failed_ack(mocker, aux_inst):
    mocker.patch.object(aux_inst, "run_command", return_value=True)
    mock_create = mocker.patch.object(aux_inst, "create_instance")
    mock_delete = mocker.patch.object(aux_inst, "delete_instance")
    mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=False
    )

    state = aux_inst.send_abort_command(timeout=10)

    mock_create.assert_called()
    mock_delete.assert_called()
    assert state is False


@pytest.mark.parametrize(
    "command",
    [
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_TEARDOWN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_TEARDOWN)),
    ],
)
def test_send_fixture_command(mocker, aux_inst, command):
    run_mock = mocker.patch.object(aux_inst, "run_command", return_value=True)
    match_mock = mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=True
    )

    state = aux_inst.send_fixture_command(command, timeout=10)

    run_mock.assert_called_once()
    match_mock.assert_called_once()
    run_mock.assert_called_once_with(
        cmd_message=command, cmd_data=None, blocking=True, timeout_in_s=10
    )
    assert state is True


@pytest.mark.parametrize(
    "command",
    [
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_TEARDOWN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_TEARDOWN)),
    ],
)
def test_send_fixture_command_not_ack(mocker, aux_inst, command):
    mocker.patch.object(aux_inst, "run_command", return_value=None)

    state = aux_inst.send_fixture_command(command, timeout=10)

    assert state is False


@pytest.mark.parametrize(
    "command",
    [
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_SETUP)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_TEARDOWN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_TEARDOWN)),
    ],
)
def test_send_ping_command_failed_ack(mocker, aux_inst, command):
    match_mock = mocker.patch.object(
        message.Message, "check_if_ack_message_is_matching", return_value=False
    )
    run_mock = mocker.patch.object(aux_inst, "run_command", return_value=True)

    state = aux_inst.send_fixture_command(command, timeout=10)

    run_mock.assert_called()
    match_mock.assert_called()
    assert state is False


@pytest.mark.parametrize(
    "response",
    [
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_PASS)),
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_FAILED)),
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_NOT_IMPLEMENTED)),
        (message.Message(MESSAGE_TYPE.REPORT, 10)),
    ],
)
def test_evaluate_response_report(aux_inst, response):
    state = aux_inst.evaluate_response(response)

    assert state is True


@pytest.mark.parametrize(
    "response",
    [
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_SETUP)),
        (message.Message(MESSAGE_TYPE.ACK, COMMAND_TYPE.TEST_CASE_SETUP)),
        (message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_SUITE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_RUN)),
        (message.Message(MESSAGE_TYPE.ACK, COMMAND_TYPE.TEST_SUITE_TEARDOWN)),
        (message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_CASE_TEARDOWN)),
    ],
)
def test_evaluate_response_other_types(aux_inst, response):
    state = aux_inst.evaluate_response(response)

    assert state is False


@pytest.mark.parametrize(
    "response",
    [
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_PASS)),
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_FAILED)),
        (message.Message(MESSAGE_TYPE.REPORT, REPORT_TYPE.TEST_NOT_IMPLEMENTED)),
        (message.Message(MESSAGE_TYPE.REPORT, 10)),
    ],
)
def test_wait_and_get_report(aux_inst, response):
    aux_inst.queue_out.put(response)
    report = aux_inst.wait_and_get_report(blocking=False, timeout_in_s=0)

    assert report == response


@pytest.mark.parametrize(
    "response",
    [
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_SUITE_SETUP)),
        (message.Message(MESSAGE_TYPE.ACK, COMMAND_TYPE.TEST_CASE_SETUP)),
        (message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_SUITE_RUN)),
        (message.Message(MESSAGE_TYPE.COMMAND, COMMAND_TYPE.TEST_CASE_RUN)),
        (message.Message(MESSAGE_TYPE.ACK, COMMAND_TYPE.TEST_SUITE_TEARDOWN)),
        (message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_CASE_TEARDOWN)),
    ],
)
def test_evaluate_response_not_a_report(aux_inst, response):
    aux_inst.queue_out.put(response)

    report = aux_inst.wait_and_get_report(blocking=False, timeout_in_s=0)

    assert report is None


def test_wait_and_get_report_queue_empty(aux_inst):
    report = aux_inst.wait_and_get_report(blocking=False, timeout_in_s=0)

    assert report is None


def test__run_command(mocker, aux_inst):
    send_mock = mocker.patch.object(aux_inst.channel, "_cc_send")

    aux_inst._run_command(cmd_message="abcde", cmd_data=None)

    send_mock.assert_called_with(msg="abcde")


def test__run_command_exception(mocker, aux_inst, caplog):
    send_mock = mocker.patch.object(
        aux_inst.channel, "_cc_send", side_effect=AssertionError
    )

    aux_inst._run_command(cmd_message=None, cmd_data=None)

    assert "encountered error" in caplog.text


def test__receive_message(mocker, aux_inst):
    response = message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_SUITE_RUN)
    send_mock = mocker.patch.object(aux_inst.channel, "_cc_send")
    recv_mock = mocker.patch.object(
        aux_inst.channel, "_cc_receive", return_value={"msg": response}
    )

    aux_inst._receive_message(timeout_in_s=0)

    send_mock.assert_called_once()
    recv_mock.assert_called_once()
    assert aux_inst.queue_out.get_nowait() == response


def test__receive_message_no_response(mocker, aux_inst):
    send_mock = mocker.patch.object(aux_inst.channel, "_cc_send")
    recv_mock = mocker.patch.object(
        aux_inst.channel, "_cc_receive", return_value={"msg": None}
    )

    aux_inst._receive_message(timeout_in_s=0)

    send_mock.assert_not_called()

    with pytest.raises(queue.Empty):
        aux_inst.queue_out.get_nowait()


def test__receive_message_failed_ack(mocker, aux_inst):
    response = message.Message(MESSAGE_TYPE.LOG, COMMAND_TYPE.TEST_SUITE_RUN)
    send_mock = mocker.patch.object(
        aux_inst.channel, "_cc_send", side_effect=AttributeError
    )
    recv_mock = mocker.patch.object(
        aux_inst.channel, "_cc_receive", return_value={"msg": response}
    )

    aux_inst._receive_message(timeout_in_s=0)

    recv_mock.assert_called_once()
    assert aux_inst.queue_out.get_nowait() == response


def test__receive_message_response_is_ack(mocker, aux_inst):
    response = message.Message(MESSAGE_TYPE.ACK)
    send_mock = mocker.patch.object(aux_inst.channel, "_cc_send")
    recv_mock = mocker.patch.object(
        aux_inst.channel, "_cc_receive", return_value={"msg": response}
    )

    aux_inst._receive_message(timeout_in_s=0)

    send_mock.assert_not_called()
    assert aux_inst.queue_out.get_nowait() == response
