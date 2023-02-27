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

from pykiso.test_result.multi_result import MultiTestResult
from pykiso.test_result.text_result import BannerTestResult
from pykiso.test_result.xml_result import XmlTestResult


@pytest.fixture
def multi_result_instance_multiple_classes():
    return MultiTestResult(BannerTestResult, XmlTestResult)(sys.stderr, True, 1)


@pytest.fixture
def test_mock(mocker):
    return mocker.patch("pykiso.test_coordinator.test_case.BasicTest")


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("startTest", {test_mock}),
        ("startTestRun", {}),
        ("stopTestRun", {}),
        ("stop", {}),
        ("stopTest", {test_mock}),
        ("addFailure", {test_mock, Exception}),
        ("addSuccess", {test_mock}),
        ("addSkip", {test_mock, "reason"}),
        ("addUnexpectedSuccess", {test_mock}),
        ("addExpectedFailure", {test_mock, Exception}),
        ("addSubTest", {test_mock, "subtest", Exception}),
        ("addError", {test_mock, Exception}),
    ],
)
def test_call_function(
    mocker, multi_result_instance_multiple_classes, name_function, argument
):
    mock_xmltestresult = mocker.patch.object(XmlTestResult, name_function)
    mock_bannertestresult = mocker.patch.object(BannerTestResult, name_function)

    getattr(multi_result_instance_multiple_classes, name_function)(*argument)

    mock_xmltestresult.assert_called_once_with(*argument)
    mock_bannertestresult.assert_called_once_with(*argument)


def test___getattr__(multi_result_instance_multiple_classes, test_mock, mocker):
    mocker.patch("pykiso.test_result.xml_result.XmlTestResult.getDescription")
    mocker.patch("json.dumps")
    reason = "test"

    multi_result_instance_multiple_classes.addSkip(test_mock, reason)

    assert multi_result_instance_multiple_classes.skipped == [(test_mock, reason)]


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("getDescription", {test_mock}),
        ("printErrors", {}),
        ("printErrorList", {"reason", Exception}),
    ],
)
def test_function_with_one_call_bannertestresult(
    multi_result_instance_multiple_classes, mocker, name_function, argument
):
    mock_bannertestresult = mocker.patch.object(BannerTestResult, name_function)

    getattr(multi_result_instance_multiple_classes, name_function)(*argument)

    mock_bannertestresult.assert_called_once_with(*argument)


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("getDescription", {test_mock}),
        ("printErrors", {}),
        ("printErrorList", {"reason", Exception}),
    ],
)
def test_function_with_one_call_xmltestresult(mocker, name_function, argument):
    mock_xmltestresult = mocker.patch.object(XmlTestResult, name_function)

    getattr(MultiTestResult(XmlTestResult, XmlTestResult), name_function)(*argument)

    mock_xmltestresult.assert_called_once_with(*argument)


def test_error_occured(multi_result_instance_multiple_classes):

    error_occured = multi_result_instance_multiple_classes.error_occurred

    assert error_occured is False


def test_generate_reports(multi_result_instance_multiple_classes, mocker):
    mock_generate_reports = mocker.patch.object(XmlTestResult, "generate_reports")

    multi_result_instance_multiple_classes.generate_reports("test_runner")

    mock_generate_reports.assert_called_once_with("test_runner")
