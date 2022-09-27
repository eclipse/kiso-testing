##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys
from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from pykiso.test_result.text_result import ResultStream

DUMMY_FILE = "dummy.txt"


@pytest.fixture()
def mock_stderr(mocker):
    return mocker.patch("sys.stderr")


@pytest.fixture()
def mock_open(mocker):
    return mocker.patch("builtins.open", return_value=MagicMock())


class TestResultStream:

    test_result_inst = None

    @pytest.fixture()
    def test_result_instance(self, mock_stderr, mock_open):
        return ResultStream(DUMMY_FILE)

    @pytest.mark.parametrize(
        "provided_file, expected_type, expected_type_ctx, close_calls",
        [
            (None, nullcontext, type(sys.stderr), 0),
            ("my_file", ResultStream, ResultStream, 1),
        ],
    )
    def test_open(
        self,
        mocker,
        mock_open,
        provided_file,
        expected_type,
        expected_type_ctx,
        close_calls,
    ):
        mock_close = mocker.patch.object(ResultStream, "close", return_value=None)

        stream = ResultStream(provided_file)
        assert type(stream) == expected_type

        del stream

        with ResultStream(provided_file) as stream:
            assert type(stream) == expected_type_ctx

        assert mock_close.call_count == close_calls

    def test_constructor(self, mock_open):
        stream = ResultStream(DUMMY_FILE)

        assert isinstance(stream, ResultStream)
        mock_open.assert_called_once_with(DUMMY_FILE, mode="a")

    def test_write(self, test_result_instance):
        to_write = "data"
        test_result_instance.write(to_write)
        test_result_instance.stderr.write.assert_called_once_with(to_write)
        test_result_instance.file.write.assert_called_once_with(to_write)

    def test_flush(self, mocker, test_result_instance):
        mock_fsync = mocker.patch("os.fsync")

        test_result_instance.flush()

        test_result_instance.stderr.flush.assert_called_once()
        test_result_instance.file.flush.assert_called_once()
        test_result_instance.file.fileno.assert_called_once()
        mock_fsync.assert_called_once()

    def test_close(self, test_result_instance):
        assert test_result_instance.stderr is not None
        assert test_result_instance.file is not None

        test_result_instance.close()

        assert test_result_instance.stderr is None
        assert test_result_instance.file is None
