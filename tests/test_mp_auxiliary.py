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

from pykiso.interfaces.mp_auxiliary import MpAuxiliaryInterface


@pytest.fixture
def MpAuxiliaryInterface_constructor(mocker):
    class MpAuxinterface(MpAuxiliaryInterface):
        def __init__(self):
            super().__init__(name="mp_aux")

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _create_auxiliary_instance.return_value = True
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _delete_auxiliary_instance.return_value = True
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _abort_command.return_value = "Test"
        _receive_message = mocker.stub(name="_receive_message")
        _receive_message.return_value = "Test"

    return MpAuxinterface()


def test_create_instance(mocker, MpAuxiliaryInterface_constructor):
    mock_get = mocker.patch.object(MpAuxiliaryInterface_constructor.queue_out, "get")
    mock_get.return_value = True

    result_create_inst = MpAuxiliaryInterface_constructor.create_instance()
    assert result_create_inst is True
    assert MpAuxiliaryInterface_constructor.is_instance is True
    assert (
        MpAuxiliaryInterface_constructor.queue_in.get() == "create_auxiliary_instance"
    )
    mock_get.assert_called()


def test_delete_instance(mocker, MpAuxiliaryInterface_constructor):
    mock_get = mocker.patch.object(MpAuxiliaryInterface_constructor.queue_out, "get")
    mock_get.return_value = True

    result_create_inst = MpAuxiliaryInterface_constructor.delete_instance()
    assert result_create_inst is True
    assert MpAuxiliaryInterface_constructor.is_instance is True
    assert (
        MpAuxiliaryInterface_constructor.queue_in.get() == "delete_auxiliary_instance"
    )
    mock_get.assert_called()


def test_initialize_logger(mocker, MpAuxiliaryInterface_constructor):
    assert MpAuxiliaryInterface_constructor.logger is None
    MpAuxiliaryInterface_constructor.initialize_loggers()
    assert isinstance(MpAuxiliaryInterface_constructor.logger, logging.Logger)
    assert MpAuxiliaryInterface_constructor.logger.level == logging.DEBUG


@pytest.mark.parametrize(
    "is_instance, request_value",
    [
        (False, "create_auxiliary_instance"),
        (True, "delete_auxiliary_instance"),
        (True, ("command", "test", "test2")),
        (True, "abort"),
        (True, "Test"),
    ],
)
def test_run(
    mocker,
    MpAuxiliaryInterface_constructor,
    is_instance,
    request_value,
    caplog,
):
    spy_logger = mocker.patch.object(
        MpAuxiliaryInterface_constructor, "initialize_loggers"
    )
    mock_event_is_set = mocker.patch(
        "multiprocessing.synchronize.Event.is_set", side_effect=[False, True]
    )
    mock_queue_empty = mocker.patch.object(
        MpAuxiliaryInterface_constructor.queue_in, "empty"
    )
    mock_queue_empty.return_value = False
    mock_queue_get_no_wait = mocker.patch.object(
        MpAuxiliaryInterface_constructor.queue_in, "get_nowait"
    )

    MpAuxiliaryInterface_constructor.logger = logging.getLogger("__name__")

    mock_queue_get_no_wait.return_value = request_value
    MpAuxiliaryInterface_constructor.is_instance = is_instance

    with caplog.at_level(logging.INFO):
        MpAuxiliaryInterface_constructor.run()
    spy_logger.assert_called()

    assert mock_event_is_set.call_count == 2
    mock_queue_empty.assert_called()

    if request_value == "Test":
        assert "Unknown request 'Test', will not be processed!" in caplog.text
        assert f"Aux status: {MpAuxiliaryInterface_constructor.__dict__}" in caplog.text
