##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import builtins
import logging
import multiprocessing
import pathlib
import threading

import pytest

from pykiso.lib.auxiliaries.record_auxiliary import (
    RecordAuxiliary,
    StringIOHandler,
)


@pytest.fixture
def mock_channel(mocker):
    class Channel:
        def __init__(self, name=None):
            self.name = name

        open = mocker.stub(name="open")
        close = mocker.stub(name="close")
        cc_receive = mocker.stub(name="cc_receive")

    return Channel(name="test-channel")


@pytest.mark.parametrize(
    "is_active, manual_start_record, expected_start_record",
    [
        (False, False, False),
        (True, False, True),
        (True, True, False),
        (False, True, False),
    ],
)
def test_constructor(
    is_active, manual_start_record, expected_start_record, mocker, mock_channel
):
    mock_start_record = mocker.patch.object(RecordAuxiliary, "start_recording")

    record_aux = RecordAuxiliary(
        com=mock_channel,
        is_active=is_active,
        timeout=123,
        log_folder_path="log_folder_path",
        max_file_size=456,
        multiprocess=False,
        manual_start_record=manual_start_record,
    )

    assert record_aux.is_proxy_capable is True
    assert record_aux.channel == mock_channel
    assert record_aux.is_active is is_active
    assert record_aux.timeout == 123
    assert record_aux.cursor == 0
    assert record_aux.log_folder_path == "log_folder_path"
    assert isinstance(record_aux._data, StringIOHandler)
    assert record_aux.max_file_size == 456
    assert record_aux._receive_thread_or_process is None
    assert record_aux.stop_receive_event is None
    assert record_aux.multiprocess is False

    if expected_start_record:
        mock_start_record.assert_called_once()
    else:
        mock_start_record.assert_not_called()


def test_instance_passive(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=False)
    assert record_aux._create_auxiliary_instance()
    mock_channel.open.assert_called_once()
    record_aux.stop()
    mock_channel.close.assert_called_once()


def test_instance_active(mocker, mock_channel):
    thread_mock = mocker.patch.object(threading.Thread, "start", return_value=None)
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    assert record_aux._create_auxiliary_instance()
    thread_mock.assert_called_once()

    thread_mock = mocker.patch.object(threading.Thread, "is_alive", return_value=True)
    thread_mock = mocker.patch.object(threading.Thread, "join", return_value=None)
    record_aux.stop()


def test_instance_active_error_thread_start(caplog, mocker, mock_channel):
    mock_channel.open.side_effect = Exception("666")

    record_aux = RecordAuxiliary(mock_channel, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux._create_auxiliary_instance()

    assert "Error encountered during channel creation" in caplog.text


def test_delete_aux_error(caplog, mocker, mock_channel):
    mocker.patch.object(mock_channel, "close", side_effect=Exception("666"))
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux._delete_auxiliary_instance()
    assert "Unable to close Channel." in caplog.text


@pytest.mark.parametrize(
    "data, expected_data",
    [
        (
            {
                "msg": b"test",
                "remote_id": 0,
            },
            "\n0    test",
        ),
        ({"msg": b"test"}, "\ntest"),
        (
            {
                "msg": b"\x00\x01\x02\xcc\xcc\xee\xff",
                "remote_id": 55,
            },
            "\n55    000102cccceeff",
        ),
        ({"msg": b"\x00\x01\x02\xcc\xcc\xee\xff"}, "\n000102cccceeff"),
    ],
)
def test_receive(data, expected_data, mocker, mock_channel):
    event_mock = mocker.patch.object(
        threading.Event, "is_set", side_effect=[False, True]
    )
    mocker.patch.object(threading.Thread, "start", return_value=None)
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    record_aux.multiprocess = True
    mock_dump_to_file = mocker.patch.object(record_aux, "dump_to_file")
    mocker.patch.object(record_aux.channel, "cc_receive", return_value=data)
    mock_set_data = mocker.patch.object(record_aux, "set_data")

    record_aux.receive()

    assert event_mock.call_count == 2
    mock_channel.open.assert_called_once()
    mock_channel.close.assert_called_once()
    mock_set_data.assert_called_once_with(expected_data)
    mock_dump_to_file.assert_called()


def test_receive_open_error(caplog, mocker, mock_channel):
    mocker.patch.object(mock_channel, "open", side_effect=Exception("666"))
    mocker.patch.object(threading.Thread, "start")

    record_aux = RecordAuxiliary(mock_channel, is_active=False)

    with caplog.at_level(logging.INFO):
        record_aux.receive()
    assert "Error encountered while channel creation." in caplog.text


def test_receive_close_error(caplog, mocker, mock_channel):
    mock_channel.close.side_effect = [Exception("666")]
    mocker.patch.object(threading.Thread, "start")
    mock_event = mocker.Mock()
    mock_event.is_set.side_effect = [False, True]

    record_aux = RecordAuxiliary(mock_channel, is_active=False)
    record_aux.stop_receive_event = mock_event
    mocker.patch.object(record_aux, "set_data", side_effect="Received data: test")

    with caplog.at_level(logging.INFO):
        record_aux.receive()
    assert "Error encountered while closing channel." in caplog.text


@pytest.mark.parametrize(
    "multiprocess",
    [False, True],
)
def test_start_recording(multiprocess, mocker, mock_channel):
    mock_thread_start = mocker.patch.object(threading.Thread, "start")
    mock_process_start = mocker.patch.object(multiprocessing.Process, "start")
    mock_clear_buffer = mocker.patch.object(RecordAuxiliary, "clear_buffer")

    record_aux = RecordAuxiliary(
        mock_channel, is_active=True, multiprocess=multiprocess
    )

    # simulate a second start in a row
    mocker.patch.object(
        record_aux._receive_thread_or_process, "is_alive", return_value=True
    )
    record_aux.start_recording()

    if multiprocess:
        mock_process_start.assert_called_once()
        assert isinstance(
            record_aux.stop_receive_event, multiprocessing.synchronize.Event
        )
    else:
        mock_thread_start.assert_called_once()
        assert isinstance(record_aux.stop_receive_event, threading.Event)
    mock_clear_buffer.assert_called_once()


def test_stop_and_resume(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=False)

    assert record_aux._create_auxiliary_instance()
    mock_channel.open.assert_called_once()

    record_aux.stop_recording()
    assert record_aux._delete_auxiliary_instance() is True

    record_aux.start_recording()
    assert record_aux._create_auxiliary_instance() is True


def test_size_too_large(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    mock_channel.cc_receive.return_value = {"msg": "test".encode()}
    mock_event = mocker.Mock()
    mock_event.is_set.side_effect = [False, False, True]

    record_aux = RecordAuxiliary(mock_channel, is_active=True, max_file_size=1)
    record_aux.stop_receive_event = mock_event

    with caplog.at_level(logging.ERROR):
        record_aux.receive()
    assert "Data size too large" in caplog.text


def test_display_new_log(mocker, caplog, mock_channel):
    mocker.patch.object(
        mock_channel, "cc_receive", return_value={"msg": b"\x12\x34\x56"}
    )
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(
        record_aux.stop_receive_event, "is_set", side_effect=[False, True]
    )
    mocker.patch.object(record_aux, "get_data", return_value="test")

    assert record_aux.new_log() == "test"


def test_is_message_in_log(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")

    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(record_aux, "_log_query", return_value="test test test")

    assert record_aux.is_message_in_log(message="test") is True


@pytest.mark.parametrize(
    "exception_on_failure",
    [
        True,
        False,
    ],
)
def test_wait_message_in_log_failed(mocker, caplog, exception_on_failure, mock_channel):
    mock_channel.cc_receive.return_value = "test".encode()
    mocker.patch.object(threading.Thread, "start")

    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(record_aux, "get_data", return_value="Received data: test")
    mocker.patch.object(record_aux, "is_message_in_log", return_value=False)

    if exception_on_failure is True:
        with pytest.raises(TimeoutError):
            record_aux.wait_for_message_in_log(
                message="test",
                timeout=0.1,
            )
    else:
        with caplog.at_level(logging.WARNING):
            record_aux.wait_for_message_in_log(
                message="test", timeout=0.1, exception_on_failure=False
            )
        assert "Maximum wait time for message test" in caplog.text


def test_wait_message_in_log(mocker, caplog, mock_channel):
    mock_channel.cc_receive.return_value = "test".encode()
    mocker.patch.object(threading.Thread, "start")

    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(
        record_aux._data, "get_data", return_value="Received data: test"
    )

    assert record_aux.wait_for_message_in_log(message="test", timeout=5) is True


def new_log(mocker, mock_channel):
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(
        record_aux, "get_data", return_value="Received data:\n test1 \n test2 \n test3"
    )

    assert record_aux.new_log() == "test3"


def test_regex_in_string(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(
        record_aux._data,
        "get_data",
        return_value="Received data:\n test1 \n test2 \n test3",
    )
    regex = record_aux.search_regex_current_string(regex=r"test\d")
    assert regex == ["test1", "test2", "test3"]


def test_regex_file_not_exist(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(pathlib.Path, "exists", return_value=False)

    with caplog.at_level(logging.ERROR):
        record_aux.search_regex_in_file("test", "test.log")
    assert "No such file test.log" in caplog.text


def test_regex_file(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(
        pathlib.Path,
        "read_text",
        return_value="Received data:\n test1 \n test2 \n test3",
    )
    mocker.patch.object(pathlib.Path, "exists", return_value=True)

    regex = record_aux.search_regex_in_file(regex=r"test\d", filename="test.log")
    assert regex == ["test1", "test2", "test3"]


def test_regex_folder_failed_dir_not_exist(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(pathlib.Path, "is_dir", return_value=False)

    with pytest.raises(FileNotFoundError):
        record_aux.search_regex_in_folder(regex=r"test\d")


def test_regex_folder(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(pathlib.Path, "is_dir", return_value=True)
    mocker.patch.object(
        pathlib.Path, "iterdir", return_value=["test1.log", "test2.log"]
    )
    mocker.patch.object(
        pathlib.Path,
        "read_text",
        return_value="Received data:\n test1 \n test2 \n test3",
    )

    regex = record_aux.search_regex_in_folder(regex=r"test\d")
    assert regex == {
        "test1.log": ["test1", "test2", "test3"],
        "test2.log": ["test1", "test2", "test3"],
    }


def test_clear_buffer(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    record_aux.set_data("A fresh new Log")
    assert "A fresh new Log" in record_aux.get_data()

    record_aux.clear_buffer()

    assert "A fresh new Log" not in record_aux.get_data()


def test_log_not_empty(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)

    record_aux.set_data("Received data : test")

    assert record_aux.is_log_empty() is False


def test_dumping_failed_path_not_exist(mocker, mock_channel):
    mocker.patch.object(builtins, "open")
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True, log_folder_path="test")
    record_aux.set_data("Received data : test")

    mocker.patch.object(pathlib.Path, "exists", return_value=False)
    mock_mkdir = mocker.patch.object(pathlib.Path, "mkdir")

    record_aux.dump_to_file(filename="test.log")

    mock_mkdir.assert_called_once()


def test_dumping_failed_path_log_empty(mocker, caplog, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    record_aux.set_data("Received data :")

    with caplog.at_level(logging.WARNING):
        result = record_aux.dump_to_file(filename="test.log")

    assert "Log data is empty. skip dump to file." in caplog.text
    assert result is False


def test_dumping_data(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    mocker.patch.object(pathlib.Path, "exists", return_value=True)
    mock_mkdir = mocker.patch.object(pathlib.Path, "mkdir")
    mocker.patch.object(builtins, "open")

    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    mocker.patch.object(record_aux, "get_data", return_value="Received data : test")
    mocker.patch.object(record_aux, "receive")
    record_aux._delete_auxiliary_instance()

    result = record_aux.dump_to_file(filename="test.log") is True

    mock_mkdir.assert_called_once()
    assert result is True


def test_message_in_full_log(mocker, mock_channel):
    mocker.patch.object(threading.Thread, "start")
    record_aux = RecordAuxiliary(mock_channel, is_active=True)
    record_aux.set_data("Received data : this is a test")

    assert record_aux.is_message_in_full_log(message="this") is True


def test_stop_recording(mocker, caplog, mock_channel):
    mocker.patch.object(
        mock_channel, "cc_receive", return_value={"msg": b"\x12\x34\x56"}
    )
    record_aux = RecordAuxiliary(mock_channel, is_active=True)

    with caplog.at_level(logging.INFO):
        record_aux.stop_recording()
        assert f"{record_aux.name} Recording has stopped" in caplog.text
