##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys
import pytest
import pathlib
import subprocess
import threading
import time
from pykiso import message
from pykiso.lib.auxiliaries.zephyr import ZephyrTestAuxiliary, ZephyrError, Twister
from unittest import mock
import xml.etree.ElementTree as ET


# @pytest.fixture
# def zephyr_aux():
#    return ZephyrTestAuxiliary()


@pytest.mark.parametrize(
    "twister_path, test_directory, test_directory_start, testname, testname_start, wait",
    [
        ("twister", "b", None, "testname1", "testname2", False),
        ("twister2", None, "b", "testname1", None, False),
        (None, None, "b", "testname1", None, False),
        ("twister2", "b", None, None, None, False),
        ("twister2", None, None, "testname1", "testname2", False),
    ],
)
def test_zephyr_aux(
    mocker,
    twister_path,
    test_directory,
    test_directory_start,
    testname,
    testname_start,
    wait,
):
    global mock_readline_counter
    mock_readline_counter = 0

    twister_instance = mock.MagicMock(Twister)
    twister_mock = mocker.patch(
        "pykiso.lib.auxiliaries.zephyr.Twister", return_value=twister_instance
    )

    zephyr_aux = ZephyrTestAuxiliary(twister_path, test_directory, testname, wait)
    twister_mock.assert_called_once_with(twister_path)

    if (test_directory is None and test_directory_start is None) or (
        testname is None and testname_start is None
    ):
        with pytest.raises(ZephyrError) as e:
            zephyr_aux.start_test(test_directory_start, testname_start)
    else:
        zephyr_aux.start_test(test_directory_start, testname_start)
        twister_instance.start_test.assert_called_once_with(
            test_directory_start
            if test_directory_start is not None
            else test_directory,
            testname_start if testname_start is not None else testname,
            wait,
        )

    zephyr_aux.wait_test()
    twister_instance.wait_test.assert_called_once()


def test_zephyr_aux_misc(mocker):
    zephyr_aux = ZephyrTestAuxiliary()
    zephyr_aux._create_auxiliary_instance()
    zephyr_aux._delete_auxiliary_instance()


mock_readline_counter = 0


def mock_readline():
    global mock_readline_counter
    if mock_readline_counter > 2:
        return ""
    ret = [
        b"2022-07-15 08:26:34,750 [DEBUG] zephyr:105: Twister: DEBUG   - OUTPUT:",
        b"2022-07-15 08:26:34,750 [DEBUG] zephyr:105: Twister: DEBUG   - OUTPUT: START - test_assert",
        b"2022-07-15 08:26:34,750 [DEBUG] zephyr:105: Twister: DEBUG   - OUTPUT:  PASS - test_assert in 0.0 seconds",
    ][mock_readline_counter]
    mock_readline_counter = mock_readline_counter + 1
    return ret


@pytest.mark.parametrize(
    "twister_path, test_directory, testname, wait",
    [
        ("twister", "b", "testname1", False),
        ("twister", "b", "testname1", True),
    ],
)
def test_twister(
    mocker,
    twister_path,
    test_directory,
    testname,
    wait,
):
    global mock_readline_counter
    mock_readline_counter = 0
    mock_path = mock.MagicMock()
    mocker.patch.object(pathlib.Path, "resolve", return_value=mock_path)

    mock_process = mock.MagicMock()
    mocker.patch("subprocess.Popen", return_value=mock_process)

    mock_et = mock.MagicMock()
    mocker.patch.object(ET, "parse", return_value=mock_et)

    twister = Twister(twister_path)

    mock_process.stderr.readline = mock_readline
    twister.start_test(test_directory, testname, wait)

    result = twister.wait_test()


def test_twister_aux_wait_exception(mocker):
    global mock_readline_counter
    mock_readline_counter = 0
    twister = Twister()
    with pytest.raises(ZephyrError) as e:
        twister.wait_test()


def test_twister_start_exception(mocker):
    global mock_readline_counter
    mock_readline_counter = 0
    twister = Twister()
    twister.process = 1
    with pytest.raises(ZephyrError) as e:
        twister.start_test("dir", "name")


def test_twister_parse_xunit(mocker):
    mock_et = mock.MagicMock()
    mocker.patch.object(ET, "parse", return_value=mock_et)
    twister = Twister()

    mocker.patch.object(mock_et, "get_root", return_value=mock_et)
    mocker.patch.object(mock_et, "find", return_value=mock_et)

    twister._parse_xunit("file")
