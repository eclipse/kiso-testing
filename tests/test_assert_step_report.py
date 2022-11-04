import pathlib
import sys
from collections import OrderedDict
from unittest import mock
from unittest.case import TestCase, _SubTest

import jinja2
import pytest

import pykiso.test_result.assert_step_report as assert_step_report
from pykiso import message
from pykiso.test_coordinator.test_case import RemoteTest
from pykiso.test_result.text_result import BannerTestResult
from pykiso.test_result.xml_result import TestInfo, XmlTestResult

# prevent pytest from collecting these as test cases
RemoteTest.__test__ = False
_SubTest.__test__ = False


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
def remote_test_case(mocker):
    class FakeReport:
        sub_type = message.MessageReportType.TEST_PASS

        def get_message_type(self):
            return message.MessageType.REPORT

    # auxiliary will be used in pykiso.test_execution.test_message_handler
    mock_auxiliary = mock.MagicMock()
    mock_auxiliary.send_fixture_command.return_value = True
    mock_auxiliary.wait_and_get_report.return_value = FakeReport()

    tc = RemoteTest(1, 2, [mock_auxiliary], 3, 4, 5, None, None)

    # decorate assertion performed in test_app_interaction
    tc.assertEqual = assert_step_report.assert_decorator(tc.assertEqual)

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

    subtest = _SubTest(test1, "msg", None)

    test2 = mock.MagicMock(TestInfo)
    test2.start_time = 1
    test2.stop_time = 2
    test2.elapsed_time = 1
    test2.test_name = "x.TestClassName"
    test2.test_result = mock.MagicMock()
    test2.test_result.start_time = 1
    test2.test_result.stop_time = 2
    test2.test_result.elapsed_time = 1

    result.successes = [test1, (subtest,), test2]
    result.expectedFailures = []
    result.failures = [(test2, "")]
    result.errors = []
    result.unexpectedSuccesses = []
    return result


def test_assert_decorator_no_message(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    data_to_test = True
    test_case.assertTrue(data_to_test)

    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_decorator_no_message",
        "",
        "data_to_test",
        "True",
        data_to_test,
    )


def test_assert_decorator_step_report_message(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    test_case.step_report.message = "Dummy message"
    data_to_test = True
    test_case.assertTrue(data_to_test)

    assert test_case.step_report.message == ""
    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_decorator_step_report_message",
        "Dummy message",
        "data_to_test",
        "True",
        data_to_test,
    )


def test_assert_decorator_reraise(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")
    assert_step_report.ALL_STEP_REPORT = OrderedDict()
    assert_step_report.ALL_STEP_REPORT["TestCase"] = {
        "test_list": {"test_assert_decorator_reraise": [{"succeed": True}]}
    }

    data_to_test = False
    with pytest.raises(AssertionError, match="False is not true : Dummy message"):
        test_case.assertTrue(data_to_test, msg="Dummy message")

    assert (
        assert_step_report.ALL_STEP_REPORT["TestCase"]["test_list"][
            "test_assert_decorator_reraise"
        ][-1]["succeed"]
        == False
    )
    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_decorator_reraise",
        "Dummy message",
        "data_to_test",
        "True",
        data_to_test,
    )


def test_assert_decorator_remote_test(mocker, remote_test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    remote_test_case.test_run()

    step_result.assert_called_once_with(
        "RemoteTest",
        "test_run",
        "",
        "report",
        "Equal to MessageReportType.TEST_PASS",
        message.MessageReportType.TEST_PASS,
    )


def test_assert_decorator_no_var_name(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    test_case.assertTrue(True)

    step_result.assert_called_once_with(
        "TestCase", "test_assert_decorator_no_var_name", "", "True", "True", True
    )


def test_assert_decorator_multi_input(mocker, test_case):
    step_result = mocker.patch("pykiso.test_result.assert_step_report._add_step")

    data_to_test = 4.5
    data_expected = 4.5
    test_case.assertAlmostEqual(
        data_to_test, data_expected, delta=1, msg="Test the step report"
    )

    step_result.assert_called_once_with(
        "TestCase",
        "test_assert_decorator_multi_input",
        "Test the step report",
        "data_to_test",
        "Almost Equal to 4.5; with delta=1",
        4.5,
    )


def test_generate(mocker, test_result):
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


def test_add_step():

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
