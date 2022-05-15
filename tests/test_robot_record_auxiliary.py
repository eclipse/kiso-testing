##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.auxiliaries.record_auxiliary import RecordAuxiliary
from pykiso.lib.robot_framework import record_auxiliary
from pykiso.lib.robot_framework.aux_interface import RobotAuxInterface
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture
def record_auxiliary_inst(mocker, cchannel_inst):
    mocker.patch.object(
        RobotAuxInterface, "_get_aux", return_value=RecordAuxiliary(cchannel_inst)
    )
    mocker.patch.object(ConfigRegistry, "get_auxes_by_type")

    return record_auxiliary.RecordAuxiliary()


def test_clear_buffer(mocker, record_auxiliary_inst):
    mock_buffer = mocker.patch.object(RecordAuxiliary, "clear_buffer")
    record_auxiliary_inst.clear_buffer("Test")
    mock_buffer.assert_called()


def test_stop_recording(mocker, record_auxiliary_inst):
    mock_stop_recording = mocker.patch.object(RecordAuxiliary, "stop_recording")
    record_auxiliary_inst.stop_recording("Test")
    mock_stop_recording.assert_called()


def test_start_recording(mocker, record_auxiliary_inst):
    mock_start_recording = mocker.patch.object(RecordAuxiliary, "start_recording")
    record_auxiliary_inst.start_recording("Test")
    mock_start_recording.assert_called()


def test_is_log_empty(mocker, record_auxiliary_inst):
    mock_is_log_empty = mocker.patch.object(
        RecordAuxiliary, "is_log_empty", return_value="test_is_log_empty"
    )
    result = record_auxiliary_inst.is_log_empty("Test")
    mock_is_log_empty.assert_called()
    assert "test_is_log_empty" == result


def test_dump_to_file(mocker, record_auxiliary_inst):
    mock_dump_to_file = mocker.patch.object(
        RecordAuxiliary, "dump_to_file", return_value="test_dump_to_file"
    )
    result = record_auxiliary_inst.dump_to_file("filename", "Test")
    mock_dump_to_file.assert_called()
    assert "test_dump_to_file" == result


def test_set_data(mocker, record_auxiliary_inst):
    mock_set_data = mocker.patch.object(RecordAuxiliary, "set_data")
    record_auxiliary_inst.set_data("data", "Test")
    mock_set_data.assert_called()


def test_get_data(mocker, record_auxiliary_inst):
    mock_get_data = mocker.patch.object(
        RecordAuxiliary, "get_data", return_value="Test_get_data"
    )
    result = record_auxiliary_inst.get_data("Test")
    mock_get_data.assert_called()
    assert result == "Test_get_data"


def test_new_log(mocker, record_auxiliary_inst):
    mock_new_log = mocker.patch.object(
        RecordAuxiliary, "new_log", return_value="Test_new_log"
    )
    result = record_auxiliary_inst.new_log("Test")
    mock_new_log.assert_called()
    assert result == "Test_new_log"


def test_previous_log(mocker, record_auxiliary_inst):
    mock_previous_log = mocker.patch.object(
        RecordAuxiliary, "previous_log", return_value="Test_previous_log"
    )
    result = record_auxiliary_inst.previous_log("Test")
    mock_previous_log.assert_called()
    assert result == "Test_previous_log"


def test_is_message_in_log(mocker, record_auxiliary_inst):
    mock_is_message_in_log = mocker.patch.object(
        RecordAuxiliary, "is_message_in_log", return_value="Test_is_message_in_log"
    )
    result = record_auxiliary_inst.is_message_in_log("Test", "message_test")
    mock_is_message_in_log.assert_called()
    assert result == "Test_is_message_in_log"


def test_is_message_in_full_log(mocker, record_auxiliary_inst):

    mock_is_message_in_full_log = mocker.patch.object(
        RecordAuxiliary,
        "is_message_in_full_log",
        return_value="Test_is_message_in_full_log",
    )
    result = record_auxiliary_inst.is_message_in_full_log("Test", "message")
    mock_is_message_in_full_log.assert_called()
    assert result == "Test_is_message_in_full_log"


def test_wait_for_message_in_log(mocker, record_auxiliary_inst):

    mock_wait_for_message_in_log = mocker.patch.object(
        RecordAuxiliary,
        "wait_for_message_in_log",
        return_value="Test_wait_for_message_in_log",
    )
    result = record_auxiliary_inst.wait_for_message_in_log("Test", "message")
    mock_wait_for_message_in_log.assert_called()
    assert result == "Test_wait_for_message_in_log"
