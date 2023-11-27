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

import pytest

import pykiso
from pykiso import AuxiliaryInterface, logging_initializer
from pykiso.exceptions import AuxiliaryCreationError
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture
def mock_aux(mocker):
    class MockAux(AuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            AuxiliaryInterface.__init__(self, **kwargs)

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

    class DummyAux(AuxiliaryInterface):
        def __init__(self):
            super().__init__()

        def _create_auxiliary_instance(self):
            pass

        def _delete_auxiliary_instance(self):
            pass

        def _run_command(self):
            pass

        def _receive_message(self):
            pass

    my_dummy_aux = DummyAux()
    assert hasattr(logging, "INTERNAL_INFO")
    assert hasattr(logging, "INTERNAL_DEBUG")
    assert hasattr(logging, "INTERNAL_WARNING")


def test_resume_stopped_aux(mock_aux):
    mock_aux.resume()
    mock_aux.create_instance.assert_called_once()


def test_suspend_running_aux(mock_aux):
    mock_aux.is_instance = True
    mock_aux.suspend()
    mock_aux.delete_instance.assert_called_once()


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
    mock_aux.is_instance = True
    status_code = mock_aux.run_command(cmd, data, blocking, timeout)

    assert isinstance(mock_aux.queue_in.get(), tuple)
    assert status_code
