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

from pykiso.interfaces.mp_auxiliary import (
    AuxiliaryCreationError,
    MpAuxiliaryInterface,
)


@pytest.fixture
def mp_inst(mocker):
    class ConcreteMpAux(MpAuxiliaryInterface):
        def __init__(self):
            super().__init__(name="mp_aux")

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")

    return ConcreteMpAux()


def test_create_instance(mocker, mp_inst):
    mock_put = mocker.patch.object(mp_inst.queue_in, "put")
    mock_get = mocker.patch.object(mp_inst.queue_out, "get", return_value=True)

    state = mp_inst.create_instance()

    mock_put.assert_called_with("create_auxiliary_instance")
    mock_get.assert_called_once()
    assert state is True


def test_create_instance_error(mocker, mp_inst):
    mock_put = mocker.patch.object(mp_inst.queue_in, "put")
    mock_get = mocker.patch.object(mp_inst.queue_out, "get", return_value=False)

    with pytest.raises(AuxiliaryCreationError):
        mp_inst.create_instance()


def test_delete_instance(mocker, mp_inst):
    mock_alive = mocker.patch.object(mp_inst, "is_alive", return_value=True)
    mock_put = mocker.patch.object(mp_inst.queue_in, "put")
    mock_get = mocker.patch.object(mp_inst.queue_out, "get", return_value=True)

    state = mp_inst.delete_instance()

    mock_put.assert_called_with("delete_auxiliary_instance")
    mock_get.assert_called_once()
    mock_alive.assert_called_once()
    assert mp_inst.is_instance is True
    assert state is True


def test_delete_instance_fail(mocker, mp_inst):
    mock_alive = mocker.patch.object(mp_inst, "is_alive", return_value=True)
    mock_put = mocker.patch.object(mp_inst.queue_in, "put")
    mock_get = mocker.patch.object(mp_inst.queue_out, "get", return_value=False)

    state = mp_inst.delete_instance()

    mock_put.assert_called_with("delete_auxiliary_instance")
    mock_get.assert_called_once()
    mock_alive.assert_called_once()
    assert mp_inst.is_instance is False
    assert state is False


def test_delete_instance_not_alive(mocker, mp_inst):
    mock_put = mocker.patch.object(mp_inst.queue_in, "put")
    mock_get = mocker.patch.object(mp_inst.queue_out, "get")

    state = mp_inst.delete_instance()

    mock_put.assert_not_called()
    mock_get.assert_not_called()
    assert mp_inst.is_instance is False
    assert state is None


def test_initialize_loggers(mp_inst):
    mp_inst.initialize_loggers()

    assert isinstance(mp_inst.logger, logging.Logger)
    assert mp_inst.logger.level == logging.DEBUG


def test_run_create_auxiliary_instance_command(mocker, mp_inst):
    mock_logger = mocker.patch.object(mp_inst, "initialize_loggers")
    mock_empty = mocker.patch.object(mp_inst.queue_in, "empty", return_value=False)
    mock_wait = mocker.patch.object(
        mp_inst.queue_in, "get_nowait", return_value="create_auxiliary_instance"
    )
    mock_create = mocker.patch.object(
        mp_inst, "_create_auxiliary_instance", return_value=True
    )
    mock_put = mocker.patch.object(mp_inst.queue_out, "put", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_logger.assert_called_once()
        mock_create.assert_called_once()
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_delete_auxiliary_instance_command(mocker, mp_inst):
    mp_inst.is_instance = True
    mock_logger = mocker.patch.object(mp_inst, "initialize_loggers")
    mock_empty = mocker.patch.object(mp_inst.queue_in, "empty", return_value=False)
    mock_wait = mocker.patch.object(
        mp_inst.queue_in, "get_nowait", return_value="delete_auxiliary_instance"
    )
    mock_delete = mocker.patch.object(
        mp_inst, "_delete_auxiliary_instance", return_value=True
    )
    mock_put = mocker.patch.object(mp_inst.queue_out, "put", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_logger.assert_called_once()
        mock_delete.assert_called_once()
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_abort_command(mocker, mp_inst):
    mp_inst.is_instance = True
    mock_logger = mocker.patch.object(mp_inst, "initialize_loggers")
    mock_empty = mocker.patch.object(mp_inst.queue_in, "empty", return_value=False)
    mock_wait = mocker.patch.object(
        mp_inst.queue_in, "get_nowait", return_value="abort"
    )
    mock_abort = mocker.patch.object(mp_inst, "_abort_command", return_value=True)
    mock_put = mocker.patch.object(mp_inst.queue_out, "put", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_logger.assert_called_once()
        mock_abort.assert_called_once()
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_command(mocker, mp_inst):
    mp_inst.is_instance = True
    mock_logger = mocker.patch.object(mp_inst, "initialize_loggers")
    mock_empty = mocker.patch.object(mp_inst.queue_in, "empty", return_value=False)
    mock_wait = mocker.patch.object(
        mp_inst.queue_in, "get_nowait", return_value=("command", "supr_command", 1)
    )
    mock_cmd = mocker.patch.object(mp_inst, "_run_command", return_value=True)
    mock_put = mocker.patch.object(mp_inst.queue_out, "put", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_logger.assert_called_once()
        mock_cmd.assert_called_with("supr_command", 1)
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_unknown_command(mocker, mp_inst):
    mp_inst.is_instance = True
    mp_inst.initialize_loggers()
    mock_empty = mocker.patch.object(mp_inst.queue_in, "empty", return_value=False)
    mock_wait = mocker.patch.object(
        mp_inst.queue_in, "get_nowait", return_value=("fake_coammnd", "supr_command", 1)
    )
    mock_warning = mocker.patch.object(
        mp_inst.logger, "warning", side_effect=ValueError
    )

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_warning.assert_called_once()
        mock_wait.assert_called_once()


def test_run_receive_message(mocker, mp_inst):
    mp_inst.is_instance = True
    mock_recv = mocker.patch.object(mp_inst, "_receive_message", return_value=True)
    mock_put = mocker.patch.object(mp_inst.queue_out, "put", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()

        mock_recv.assert_called_with(timeout_in_s=0)
        mock_put.assert_called_with(True)


def test_run_free_cpu_usage(mocker, mp_inst):
    mock_sleep = mocker.patch("time.sleep", side_effect=ValueError)

    with pytest.raises(ValueError):
        mp_inst.run()
        mock_sleep.assert_called_with(0.050)


def test_run_stop_command_running_instance(mocker, mp_inst):
    mp_inst.is_instance = True
    mock_set = mocker.patch.object(mp_inst.stop_event, "is_set", return_value=True)
    mock_delete = mocker.patch.object(
        mp_inst, "_delete_auxiliary_instance", return_value=True
    )

    mp_inst.run()

    mock_delete.assert_called_once()
    mock_set.assert_called_once()


def test_run_stop_command_not_running_instance(mocker, mp_inst):
    mp_inst.is_instance = False
    mock_set = mocker.patch.object(mp_inst.stop_event, "is_set", return_value=True)
    mock_delete = mocker.patch.object(mp_inst, "_delete_auxiliary_instance")

    mp_inst.run()

    mock_delete.assert_not_called()
    mock_set.assert_called_once()
