##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import time
from multiprocessing.connection import deliver_challenge

import pytest

import pykiso
from pykiso import (
    AuxiliaryInterface,
    MpAuxiliaryInterface,
    SimpleAuxiliaryInterface,
    logging_initializer,
)
from pykiso.auxiliary import AuxiliaryCommon
from pykiso.exceptions import AuxiliaryCreationError
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture
def mock_aux(mocker):
    class MockAux(AuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            super().__init__(**kwargs)

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")
        create_instance = mocker.stub(name="create_instance")
        delete_instance = mocker.stub(name="delete_instance")
        run = mocker.stub(name="run")
        start = mocker.stub(name="start")
        is_alive = mocker.stub(name="is_alive")
        join = mocker.stub(name="join")

    mocker.patch.object(time, "sleep")

    return MockAux()


@pytest.fixture
def mock_thread_aux(mocker):
    class MockThreadAux(AuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            super().__init__(**kwargs)

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")

    return MockThreadAux()


@pytest.fixture
def mock_mp_aux(mocker):
    class MockMpAux(MpAuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            logging_initializer.log_options = logging_initializer.LogOptions(
                None, "ERROR", None, False
            )
            self.param_1 = param_1
            self.param_2 = param_2
            super().__init__(name="mp_aux", **kwargs)

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")

    return MockMpAux()


@pytest.fixture
def mock_simple_aux(mocker):
    class MockSimpleAux(SimpleAuxiliaryInterface):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")

    return MockSimpleAux()


def test_add_internal_log_levels():

    # does the opposite of add_logging_level, so log levels addition can be tested
    def del_logging_level(level_name):
        method_name = level_name.lower()

        delattr(logging, level_name)
        delattr(logging.getLoggerClass(), method_name)
        delattr(logging, method_name)

    del_logging_level("INTERNAL_WARNING")
    del_logging_level("INTERNAL_INFO")
    del_logging_level("INTERNAL_DEBUG")

    assert not hasattr(logging, "INTERNAL_INFO")
    assert not hasattr(logging, "INTERNAL_DEBUG")
    assert not hasattr(logging, "INTERNAL_WARNING")

    class DummyAux(AuxiliaryCommon):
        def __init__(self):
            super().__init__()

        def create_instance(self):
            pass

        def delete_instance(self):
            pass

        def run(self):
            pass

    my_dummy_aux = DummyAux()
    assert hasattr(logging, "INTERNAL_INFO")
    assert hasattr(logging, "INTERNAL_DEBUG")
    assert hasattr(logging, "INTERNAL_WARNING")


def test_thread_aux_raise_creation_error(mock_thread_aux):
    mock_thread_aux.queue_out.put(False)
    with pytest.raises(AuxiliaryCreationError):
        mock_thread_aux.create_instance()


def test_mp_aux_raise_creation_error(mock_mp_aux):

    mock_mp_aux.queue_out.put(False)
    with pytest.raises(AuxiliaryCreationError):
        mock_mp_aux.create_instance()


def test_simple_aux_raise_creation_error(mocker, mock_simple_aux):
    mocker.patch.object(
        mock_simple_aux, "_create_auxiliary_instance", return_value=False
    )

    with pytest.raises(AuxiliaryCreationError):
        mock_simple_aux.create_instance()


def test_lock_it(mock_aux):
    is_lock = mock_aux.lock_it(1)
    assert is_lock


def test_unlock_it(mock_aux):
    mock_aux.lock_it(1)
    is_unlock = mock_aux.unlock_it()
    is_lock = mock_aux.lock_it(1)
    assert is_lock


def test_resume_stopped_aux(mock_aux):
    mock_aux.resume()
    mock_aux.create_instance.assert_called_once()


def test_resume_running_aux(mock_aux):
    mock_aux.is_instance = True
    mock_aux.resume()
    mock_aux.create_instance.assert_not_called()


def test_suspend_running_aux(mock_aux):
    mock_aux.is_instance = True
    mock_aux.suspend()
    mock_aux.delete_instance.assert_called_once()


def test_suspend_already_stopped(mock_aux):
    mock_aux.suspend()
    mock_aux.delete_instance.assert_not_called()


def test_stop_without_copy(mock_aux):
    mock_aux.stop()
    assert mock_aux.stop_event.is_set()


def test_stop_with_copy(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    mock_aux.create_copy()
    mock_aux.stop()

    assert mock_aux._aux_copy is None
    assert mock_aux.stop_event.is_set()


@pytest.mark.parametrize(
    "blocking, timeout",
    [
        (True, 1),
        (True, 0),
        (False, None),
        (False, 1),
    ],
)
def test_wait_and_get_report(mock_aux, blocking, timeout):
    mock_aux.queue_out.put(True)
    report = mock_aux.wait_and_get_report(blocking, timeout)
    assert report


def test_wait_and_get_report_empty(mock_aux):
    response = mock_aux.wait_and_get_report()
    assert response is None


@pytest.mark.parametrize(
    "blocking, timeout",
    [
        (True, 1),
        (True, 0),
        (False, None),
        (False, 1),
    ],
)
def test_abort_command(mock_aux, blocking, timeout):
    mock_aux.queue_out.put(True)
    status_code = mock_aux.abort_command(blocking, timeout)

    assert mock_aux.queue_in.get() == "abort"
    assert status_code


def test_abort_command_empty(mock_aux):
    status_code = mock_aux.abort_command(True, 0)

    assert status_code is False


@pytest.mark.parametrize(
    "cmd, data, blocking, timeout",
    [
        ("Test", None, True, 1),
        ("Test", [1, 2, 3], True, 0),
        ("Test", None, False, None),
        ("Test", b"\01", False, 1),
    ],
)
def test_run_command(mock_aux, cmd, data, blocking, timeout):
    mock_aux.queue_out.put(True)
    status_code = mock_aux.run_command(cmd, data, blocking, timeout)

    assert isinstance(mock_aux.queue_in.get(), tuple)
    assert status_code


def test_run_command_empty(mock_aux):
    status_code = mock_aux.run_command("Test", "abc", True, 0)

    assert status_code is False


def test_create_copy_args_exception(mock_aux):
    with pytest.raises(Exception):
        mock_aux.create_copy(1, 2, 3)


def test_create_copy_unknowned_params_exception(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_none": 10}
    )

    with pytest.raises(Exception):
        mock_aux.create_copy()


def test_create_copy_existing_copy(mock_aux):
    mock_aux._aux_copy = True
    copy = mock_aux.create_copy()

    assert copy


def test_create_copy_without_params(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    copy = mock_aux.create_copy()

    assert mock_aux._aux_copy is not None
    assert copy is not None
    copy.create_instance.assert_called_once()
    copy.start.assert_called_once()


def test_create_copy_with_params(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    copy = mock_aux.create_copy(param_1=30, param_2=False)

    assert copy.param_1 == 30
    assert copy.param_1 != mock_aux.param_1
    assert copy.param_2 is False
    assert copy.param_2 != mock_aux.param_2
    copy.create_instance.assert_called_once()
    copy.start.assert_called_once()


def test_create_copy_alive_original(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    mocker.patch.object(mock_aux, "is_alive", return_value=True)
    mocker.patch.object(mock_aux, "suspend", return_value=True)
    mock_aux.is_instance = True

    copy = mock_aux.create_copy()

    mock_aux.suspend.assert_called_once()
    copy.create_instance.assert_called_once()
    copy.start.assert_called_once()


def test_create_copy_auto_start_disable(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )

    copy = mock_aux.create_copy(param_1=30, param_2=False, auto_start=False)

    copy.create_instance.assert_not_called()
    copy.start.assert_not_called()


def test_destroy_copy_not_alive(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    mocker.patch.object(mock_aux, "is_alive", return_value=False)
    mock_aux.create_copy()
    mock_aux.destroy_copy()

    assert mock_aux._aux_copy is None


def test_destroy_copy_alive(mocker, mock_aux):
    mocker.patch.object(
        ConfigRegistry, "get_aux_config", return_value={"param_1": 10, "param_2": True}
    )
    mocker.patch.object(mock_aux, "is_alive", return_value=True)
    mock_aux.create_copy()
    mock_aux.destroy_copy()

    assert mock_aux._aux_copy is None
