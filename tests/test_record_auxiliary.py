##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import threading

import pytest

from pykiso.lib.auxiliaries.record_auxiliary import RecordAuxiliary


def test_instance_passive(mocker):
    com = mocker.MagicMock()
    record_aux = RecordAuxiliary(com, is_active=False)
    assert record_aux._create_auxiliary_instance()
    com.open.assert_called_once()
    record_aux.stop()
    com.close.assert_called_once()


def test_instance_active(mocker):
    com_mock = mocker.MagicMock()
    thread_mock = mocker.patch.object(threading.Thread, "start", return_value=None)
    record_aux = RecordAuxiliary(com_mock, is_active=True)
    assert record_aux._create_auxiliary_instance()
    thread_mock.assert_called_once()

    thread_mock = mocker.patch.object(threading.Thread, "is_alive", return_value=True)
    thread_mock = mocker.patch.object(threading.Thread, "join", return_value=None)
    record_aux.stop()


def test_instance_active_error_thread_start(caplog, mocker):
    com_mock = mocker.MagicMock()
    mocker.patch.object(threading.Thread, "start", side_effect=Exception("666"))

    record_aux = RecordAuxiliary(com_mock, is_active=True)

    with caplog.at_level(logging.INFO):
        record_aux._create_auxiliary_instance()

    assert "Error encountered during channel creation" in caplog.text


def test_delete_aux_error(caplog, mocker):
    com_mock = mocker.MagicMock()
    mocker.patch.object(com_mock, "close", side_effect=Exception("666"))
    record_aux = RecordAuxiliary(com_mock, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux._delete_auxiliary_instance()
    assert "Unable to close Channel." in caplog.text


def test_receive(mocker):
    com_mock = mocker.MagicMock()

    event_mock = mocker.patch.object(
        threading.Event, "is_set", side_effect=[False, True]
    )
    record_aux = RecordAuxiliary(com_mock, is_active=True)

    record_aux.receive()
    assert event_mock.call_count == 2
    com_mock.open.assert_called_once()
    com_mock.close.assert_called_once()


def test_receive_open_error(caplog, mocker):
    com_mock = mocker.MagicMock()
    mocker.patch.object(com_mock, "open", side_effect=Exception("666"))

    record_aux = RecordAuxiliary(com_mock, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux.receive()
    assert "Error encountered during channel creation." in caplog.text


def test_receive_close_error(caplog, mocker):
    com_mock = mocker.MagicMock()
    mocker.patch.object(com_mock, "close", side_effect=Exception("666"))

    mocker.patch.object(threading.Event, "is_set", side_effect=[False, True])
    record_aux = RecordAuxiliary(com_mock, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux.receive()
    assert "Error encountered during closing channel." in caplog.text
