import pathlib
import sys
from collections import OrderedDict
from unittest import TestCase, mock

import jinja2
import pytest

import pykiso.test_result.assert_step_report as assert_step_report
from pykiso.test_result.text_result import BannerTestResult, TestCase
from pykiso.test_result.xml_result import TestInfo, XmlTestResult


@pytest.fixture
def test_case():
    tc = TestCase()
    # decorate 2 different assert
    tc.assertTrue = assert_step_report.assert_decorator(tc.assertTrue)
    tc.assertAlmostEqual = assert_step_report.assert_decorator(tc.assertAlmostEqual)

    # Add the step-report parameters
    tc.step_report = assert_step_report.StepReportData(
        header={}, message="", success=True, continue_on_error=False, current_table=None
    )

    return tc


@pytest.fixture
def test_result():
    result = mock.MagicMock(spec=BannerTestResult(sys.stderr, False, 0))

    test1 = TestCase()
    test1.start_time = 1
    test1.stop_time = 2
    test1.elapsed_time = 1

    test2 = mock.MagicMock(TestInfo)
    test2.start_time = 1
    test2.stop_time = 2
    test2.elapsed_time = 1
    test2.test_name = "x.TestClassName"
    test2.test_result = mock.MagicMock()
    test2.test_result.start_time = 1
    test2.test_result.stop_time = 2
    test2.test_result.elapsed_time = 1

    result.successes = [test1, test2]
    result.expectedFailures = []
    result.failures = [(test2, "")]
    result.errors = []
    result.unexpectedSuccesses = []
    return result


def test_assert_step_report_single_input(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    data_to_test = True
    test_case.assertTrue(data_to_test)

    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_step_report_single_input",
        "",
        "data_to_test",
        "True",
        True,
    )


def test_assert_step_report_no_var_name_test(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    test_case.assertTrue(True)

    step_result.assert_called_once_with(
        "TestCase", "test_assert_step_report_no_var_name_test", "", "True", "True", True
    )


def test_assert_step_report_message(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    data_to_test = True
    test_case.assertTrue(data_to_test, "message")

    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_step_report_message",
        "message",
        "data_to_test",
        "True",
        True,
    )


def test_assert_step_report_multi_input(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    data_to_test = 4.5
    data_expected = 4.5
    test_case.assertAlmostEqual(
        data_to_test, data_expected, delta=1, msg="Test the step report"
    )

    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_step_report_multi_input",
        "Test the step report",
        "data_to_test",
        "Almost Equal to 4.5; with delta=1",
        4.5,
    )


def test_assert_step_report_generate(mocker, test_result):
    assert_step_report.ALL_STEP_REPORT = OrderedDict()
    assert_step_report.ALL_STEP_REPORT["TestClassName"] = OrderedDict()
    assert_step_report.ALL_STEP_REPORT["TestClassName"]["time_result"] = OrderedDict()
    assert_step_report.ALL_STEP_REPORT["TestClassName"]["time_result"]["Start Time"] = 1
    assert_step_report.ALL_STEP_REPORT["TestClassName"]["time_result"]["End Time"] = 2
    assert_step_report.ALL_STEP_REPORT["TestClassName"]["time_result"][
        "Elapsed Time"
    ] = 1

    jinja2.FileSystemLoader = mock_loader = mock.MagicMock()
    jinja2.Environment = mock_environment = mock.MagicMock()

    mock_path = mock.MagicMock()
    mocker.patch.object(pathlib.Path, "resolve", return_value=mock_path)

    assert_step_report.generate_step_report(test_result, "step_report.html")

    mock_path.parent.mkdir.assert_called_once()


def test_assert_step_report_add_step(mocker):

    assert_step_report.ALL_STEP_REPORT["TestCase"] = OrderedDict()
    assert_step_report.ALL_STEP_REPORT["TestCase"]["test_list"] = OrderedDict()
    steplist = assert_step_report.ALL_STEP_REPORT["TestCase"]["test_list"][
        "test_assert_step_report_multi_input"
    ] = []

    assert_step_report._add_step(
        "TestCase",
        "test_assert_step_report_multi_input",
        "Test the step report",
        "data_to_test",
        "Almost Equal to 4.5; with delta=1",
        4.5,
    )
    assert len(steplist) == 1
