##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pytest

from pykiso.auxiliary import (
    AuxCommand,
    AuxiliaryCreationError,
    AuxiliaryInterface,
    AuxiliaryNotStarted,
    close_connector,
    open_connector,
    queue,
    threading,
)
from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface


@pytest.fixture
def aux_inst(mocker, cchannel_inst):
    class MockDtAux(AuxiliaryInterface):
        def __init__(self, *arg, **kwargs):
            super().__init__(name="aux")

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _run_command = mocker.stub(name="_run_command")
        _receive_message = mocker.stub(name="_receive_message")

    return MockDtAux()


@pytest.fixture
def aux_inst_with_channel(mocker, cchannel_inst):
    class MockDtAux(DTAuxiliaryInterface):
        def __init__(self, *arg, **kwargs):
            super().__init__(name="aux")
            self.channel = cchannel_inst

        @open_connector
        def _create_auxiliary_instance(self):
            return True

        @close_connector
        def _delete_auxiliary_instance(self):
            return True

        _run_command = mocker.stub(name="_run_command")
        _receive_message = mocker.stub(name="_receive_message")

    return MockDtAux()


def test_create_instance(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")
    aux_inst._create_auxiliary_instance.return_value = True

    state = aux_inst.create_instance()

    aux_inst._create_auxiliary_instance.assert_called_once()
    thread_start.assert_called()
    assert state is True


def test_create_instance_already_created(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")
    aux_inst.is_instance = True

    state = aux_inst.create_instance()

    aux_inst._create_auxiliary_instance.assert_not_called()
    thread_start.assert_not_called()
    assert state is True


def test_create_instance_exception(aux_inst):
    aux_inst._create_auxiliary_instance.return_value = False

    with pytest.raises(AuxiliaryCreationError):
        aux_inst.create_instance()


def test_create_delete_with_channel(aux_inst_with_channel, caplog):
    with caplog.at_level(logging.INTERNAL_INFO):
        result = aux_inst_with_channel.create_instance()

        assert result is True
        assert "Open TCChan channel 'test-channel'" in caplog.text

        result = aux_inst_with_channel.delete_instance()
        assert result is True
        assert "Close TCChan channel 'test-channel'" in caplog.text


def test_delete_instance(mocker, aux_inst):
    mocker.patch.object(threading.Thread, "start")
    thread_join = mocker.patch.object(threading.Thread, "join")
    aux_inst._create_auxiliary_instance.return_value = True
    aux_inst._delete_auxiliary_instance.return_value = True
    aux_inst.create_instance()

    state = aux_inst.delete_instance()

    aux_inst._delete_auxiliary_instance.assert_called_once()
    thread_join.assert_called()
    assert state is True


def test_delete_instance_already_deleted(mocker, aux_inst):
    state = aux_inst.delete_instance()

    aux_inst._delete_auxiliary_instance.assert_not_called()
    assert state is True


def test_delete_instance_fail(mocker, aux_inst):
    mocker.patch.object(threading.Thread, "start")
    thread_join = mocker.patch.object(threading.Thread, "join")
    aux_inst._create_auxiliary_instance.return_value = True
    aux_inst._delete_auxiliary_instance.return_value = False
    aux_inst.create_instance()

    state = aux_inst.delete_instance()

    aux_inst._delete_auxiliary_instance.assert_called_once()
    thread_join.assert_called()
    assert state is False


def test__start_tx_task(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")

    aux_inst._start_tx_task()

    thread_start.assert_called_once()
    assert isinstance(aux_inst.tx_thread, threading.Thread)


def test__start_tx_task_not_enable(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")
    aux_inst.tx_task_on = False

    aux_inst._start_tx_task()

    thread_start.assert_not_called()
    assert aux_inst.tx_thread is None


def test__start_rx_task(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")

    aux_inst._start_rx_task()

    thread_start.assert_called_once()
    assert isinstance(aux_inst.rx_thread, threading.Thread)


def test__start_rx_task_not_enable(mocker, aux_inst):
    thread_start = mocker.patch.object(threading.Thread, "start")
    aux_inst.rx_task_on = False

    aux_inst._start_rx_task()

    thread_start.assert_not_called()
    assert aux_inst.rx_thread is None


def test__stop_tx_task(mocker, aux_inst):
    mocker.patch.object(threading.Thread, "start")
    thread_join = mocker.patch.object(threading.Thread, "join")
    queue_put = mocker.patch.object(queue.Queue, "put")
    aux_inst._start_tx_task()

    aux_inst._stop_tx_task()

    thread_join.assert_called_once()
    queue_put.assert_called_once()


def test__stop_tx_task_not_enable(mocker, aux_inst):
    thread_join = mocker.patch.object(threading.Thread, "join")
    queue_put = mocker.patch.object(queue.Queue, "put")
    aux_inst.tx_task_on = False

    aux_inst._stop_tx_task()

    thread_join.assert_not_called()
    queue_put.assert_not_called()


def test__stop_rx_task(mocker, aux_inst):
    mocker.patch.object(threading.Thread, "start")
    thread_join = mocker.patch.object(threading.Thread, "join")
    aux_inst._start_rx_task()

    aux_inst._stop_rx_task()

    thread_join.assert_called_once()


def test__stop_rx_task_not_enable(mocker, aux_inst):
    thread_join = mocker.patch.object(threading.Thread, "join")
    aux_inst.rx_task_on = False

    aux_inst._stop_rx_task()

    thread_join.assert_not_called()


def test_start(mocker, aux_inst):
    mocker.patch.object(aux_inst, "create_instance", return_value=True)

    state = aux_inst.start()

    assert state is True


def test_stop(mocker, aux_inst):
    mocker.patch.object(aux_inst, "delete_instance", return_value=True)

    state = aux_inst.stop()

    assert state is True


def test_suspend(mocker, aux_inst):
    mocker.patch.object(aux_inst, "delete_instance", return_value=True)

    state = aux_inst.suspend()

    assert state is True


def test_resume(mocker, aux_inst):
    mocker.patch.object(aux_inst, "create_instance", return_value=True)

    state = aux_inst.resume()

    assert state is True


def test__transmit_task(aux_inst):
    aux_inst.queue_in.put(("send", b"\x01"))
    aux_inst.queue_in.put((AuxCommand.DELETE_AUXILIARY, None))

    aux_inst._transmit_task()

    aux_inst._run_command.assert_called_with("send", b"\x01")


def test__reception_task(aux_inst):
    aux_inst._receive_message.side_effect = ValueError

    with pytest.raises(ValueError):
        aux_inst._reception_task()

    aux_inst._receive_message.assert_called_with(timeout_in_s=aux_inst.recv_timeout)


def test_run_command(mocker, aux_inst):
    queue_put = mocker.patch.object(aux_inst.queue_in, "put")
    queue_get = mocker.patch.object(aux_inst.queue_out, "get", return_value=b"\x02")

    aux_inst.is_instance = True

    value = aux_inst.run_command(
        cmd_message="send", cmd_data=b"\x01", blocking=False, timeout_in_s=0
    )

    assert value == b"\x02"


def test_run_command_stop_event_set(mocker, aux_inst):
    queue_put = mocker.patch.object(aux_inst.queue_in, "put")
    queue_get = mocker.patch.object(aux_inst.queue_out, "get", return_value=b"\x02")

    aux_inst.is_instance = True
    aux_inst._stop_event.set()

    value = aux_inst.run_command(
        cmd_message="send",
        cmd_data=b"\x01",
        blocking=False,
        timeout_in_s=0,
        timeout_result="dummy",
    )

    aux_inst._stop_event.clear()

    assert queue_get.call_count == 0
    assert queue_put.call_count == 0
    assert value == "dummy"


def test_run_command_timeout(mocker, aux_inst):
    queue_put = mocker.patch.object(aux_inst.queue_in, "put")

    aux_inst.is_instance = True

    value = aux_inst.run_command(
        cmd_message="send", cmd_data=b"\x01", blocking=False, timeout_in_s=0
    )

    assert value is None


def test_run_command_timeout_with_user_defined_return(mocker, aux_inst):
    queue_put = mocker.patch.object(aux_inst.queue_in, "put")

    aux_inst.is_instance = True

    value = aux_inst.run_command(
        cmd_message="send",
        cmd_data=b"\x01",
        blocking=False,
        timeout_in_s=0,
        timeout_result="something",
    )

    assert value == "something"
    queue_put.assert_called_once()


def test_run_command_aux_not_started(mocker, aux_inst):
    queue_put = mocker.patch.object(aux_inst.queue_in, "put")

    aux_inst.is_instance = False

    with pytest.raises(AuxiliaryNotStarted):
        aux_inst.run_command(
            cmd_message="send", cmd_data=b"\x01", blocking=False, timeout_in_s=0
        )

    queue_put.assert_not_called()


def test_wait_for_queue_out(aux_inst):
    aux_inst.queue_out.put(b"\x01\x02\x03")

    value = aux_inst.wait_for_queue_out()

    assert value == b"\x01\x02\x03"


def test_wait_for_queue_out_empty(aux_inst):
    value = aux_inst.wait_for_queue_out(blocking=False, timeout_in_s=0)

    assert value is None
