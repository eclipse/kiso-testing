##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import copy
import logging
import pathlib
from unittest import TestCase, TestResult

import pytest

import pykiso
import pykiso.test_coordinator.test_execution
from pykiso.config_parser import parse_config
from pykiso.test_coordinator import test_execution
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_config_registry_and_test_execution(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, pattern_inject="*.py::MyTest*")
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "RUNNING TEST: " in output.err
    assert "END OF TEST: " in output.err
    assert "->  Passed" in output.err
    assert "->  Failed" not in output.err


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_config_registry_and_test_execution_with_pattern(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    by specifying a pattern

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, pattern_inject="my_test.py")
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "Ran 0 tests" in output.err


@pytest.mark.parametrize("tmp_test", [("aux_1", "aux_2", False)], indirect=True)
def test_config_registry_and_test_execution_with_user_tags(tmp_test, mocker):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    with additional user tags.

    Validation criteria:
        -  apply_filter called once
    """
    user_tags = {"variant": ["delta"]}
    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, user_tags=user_tags)
    ConfigRegistry.delete_aux_con()


@pytest.mark.parametrize(
    "tmp_test",
    [("collector_error_aux1", "collector_error_aux_2", False)],
    indirect=True,
)
def test_config_registry_test_collection_error(tmp_test, capsys, mocker, caplog):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    by specifying a pattern

    Validation criteria:
        -  run is executed without error
    """
    mocker.patch(
        "pykiso.test_coordinator.test_suite.tc_sort_key", side_effect=Exception
    )

    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)

    with pytest.raises(pykiso.TestCollectionError):
        test_execution.collect_test_suites(cfg["test_suite_list"])

    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "Ran 0 tests" not in output.err


def test_parse_test_selection_pattern():
    test_file_pattern = ()
    test_file_pattern = test_execution.parse_test_selection_pattern("first::")
    assert test_file_pattern.test_file == "first"
    assert test_file_pattern.test_class == None
    assert test_file_pattern.test_case == None

    test_file_pattern = test_execution.parse_test_selection_pattern(
        "first::second::third"
    )
    assert test_file_pattern.test_file == "first"
    assert test_file_pattern.test_class == "second"
    assert test_file_pattern.test_case == "third"

    test_file_pattern = test_execution.parse_test_selection_pattern("first::::third")
    assert test_file_pattern.test_file == "first"
    assert test_file_pattern.test_class == None
    assert test_file_pattern.test_case == "third"

    test_file_pattern = test_execution.parse_test_selection_pattern("::second::third")
    assert test_file_pattern.test_file == None
    assert test_file_pattern.test_class == "second"
    assert test_file_pattern.test_case == "third"


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_config_registry_and_test_execution_collect_error(tmp_test, capsys, mocker):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    by specifying a pattern

    Validation criteria:
        -  run is executed without error
    """
    mocker.patch(
        "pykiso.test_coordinator.test_suite.tc_sort_key", side_effect=Exception
    )

    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)

    with pytest.raises(pykiso.TestCollectionError):
        test_execution.collect_test_suites(cfg["test_suite_list"])

    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "Ran 0 tests" not in output.err


@pytest.mark.parametrize(
    "tmp_test",
    [("collector_error_2_aux1", "collector_error_2_aux", False)],
    indirect=True,
)
def test_config_registry_and_test_execution_collect_error(mocker, caplog, tmp_test):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    by specifying a pattern

    Validation criteria:
        -  run is executed with test collection error
    """
    mocker.patch(
        "pykiso.test_coordinator.test_execution.collect_test_suites",
        side_effect=pykiso.TestCollectionError("test"),
    )

    cfg = parse_config(tmp_test)

    with caplog.at_level(logging.ERROR):
        test_execution.execute(config=cfg)

    assert "Error occurred during test collections." in caplog.text


@pytest.mark.parametrize(
    "tmp_test", [("creation_error_aux1", "creation_error_aux2", False)], indirect=True
)
def test_config_registry_and_test_execution_test_auxiliary_creation_error(
    mocker, caplog, tmp_test
):
    """Call execute function from test_execution using
    configuration data coming from parse_config method
    by specifying a pattern

    Validation criteria:
        -  run is executed with auxiliary creation error
    """
    mocker.patch(
        "pykiso.test_coordinator.test_execution.collect_test_suites",
        side_effect=pykiso.AuxiliaryCreationError("test"),
    )

    cfg = parse_config(tmp_test)

    with caplog.at_level(logging.ERROR):
        test_execution.execute(config=cfg)

    assert "Error occurred during auxiliary creation." in caplog.text


@pytest.mark.parametrize("tmp_test", [("text_aux1", "text_aux2", False)], indirect=True)
def test_config_registry_and_test_execution_with_text_reporting(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method and
    --text option to show the test results only in console

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_test)
    report_option = "text"
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, report_option)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "RUNNING TEST: " in output.err
    assert "END OF TEST: " in output.err
    assert "->  Passed" in output.err
    assert "->  Failed" not in output.err


@pytest.mark.parametrize("tmp_test", [("fail_aux1", "fail_aux2", True)], indirect=True)
def test_config_registry_and_test_execution_fail(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method and
    --text option to show the test results only in console

    Validation criteria:
        -  run is executed with error
        -  error is shown in banner and in final result
    """
    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" in output.err
    assert "RUNNING TEST: " in output.err
    assert "END OF TEST: " in output.err
    assert "->  Failed" in output.err


@pytest.mark.parametrize(
    "tmp_test", [("juint_aux1", "juint_aux2", False)], indirect=True
)
def test_config_registry_and_test_execution_with_junit_reporting(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method and
    --junit option to show the test results in console
    and to generate a junit xml report

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_test)
    report_option = "junit"
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, report_option)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err
    assert "RUNNING TEST: " not in output.err
    assert "END OF TEST: " not in output.err
    assert "Passed" not in output.err


def test_config_registry_and_test_execution_failure_and_error_handling():
    TR_ALL_TESTS_SUCCEEDED = TestResult()
    TR_ONE_OR_MORE_TESTS_FAILED = TestResult()
    TR_ONE_OR_MORE_TESTS_FAILED.failures = [TestCase()]
    TR_ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION = TestResult()
    TR_ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION.errors = [TestCase()]
    TR_ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTIONE = TestResult()
    TR_ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTIONE.errors = [TestCase()]
    TR_ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTIONE.failures = [TestCase()]

    assert test_execution.failure_and_error_handling(TR_ALL_TESTS_SUCCEEDED) == 0
    assert test_execution.failure_and_error_handling(TR_ONE_OR_MORE_TESTS_FAILED) == 1
    assert (
        test_execution.failure_and_error_handling(
            TR_ONE_OR_MORE_TESTS_RAISED_UNEXPECTED_EXCEPTION
        )
        == 2
    )
    assert (
        test_execution.failure_and_error_handling(
            TR_ONE_OR_MORE_TESTS_FAILED_AND_RAISED_UNEXPECTED_EXCEPTIONE
        )
        == 3
    )


@pytest.mark.parametrize(
    "tc_tags ,cli_tags, is_test_running",
    [
        (None, {}, True),
        (
            {
                "variant": [
                    "omicron",
                ],
                "branch_level": [],
            },  # tc_tags
            {
                "variant": "omicron",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "variant": [
                    "omicron",
                ],
                "branch_level": [
                    "leaf",
                ],
            },  # tc_tags
            {
                "branch_level": "leaf",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "variant": [
                    "omicron",
                ],
                "branch_level": [
                    "leaf",
                ],
            },  # tc_tags
            {
                "branch_level": "bud",
            },  # cli_tags
            False,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v3"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {
                "k1": "v1",
                "k2": "v2",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v7"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {
                "k1": "v1",
                "k2": "v2",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v7"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {
                "k1": "v1",
                "k2": "v10",
            },  # cli_tags
            False,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v3"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {
                "k1": "v1",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v7"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {
                "k1": "v1",
            },  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v3"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {"k1": ["v1", "v3"]},  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v3"],
                "k2": ["v2", "v5", "v6"],
            },  # tc_tags
            {"k1": ["v1", "v3"], "k2": ["v2", "v5"]},  # cli_tags
            True,  # is_test_running
        ),
        (
            {
                "k1": ["v1", "v3"],
            },  # tc_tags
            {"k2": ["v2", "v5"]},  # cli_tags
            False,  # is_test_running
        ),
    ],
)
def test_config_registry_and_test_execution_apply_variant_filter(
    tc_tags, cli_tags, is_test_running, mocker
):
    mock_test_case = mocker.Mock()
    mock_test_case.setUp = None
    mock_test_case.tearDown = None
    mock_test_case.testMethodName = None
    mock_test_case.skipTest = lambda x: x  # return input
    mock_test_case.tag = tc_tags
    mock_test_case._testMethodName = "testMethodName"
    mock = mocker.patch(
        "pykiso.test_coordinator.test_execution.test_suite.flatten",
        return_value=[mock_test_case],
    )

    test_execution.apply_tag_filter({}, cli_tags)

    mock.assert_called_once()
    if is_test_running:
        assert mock_test_case.setUp is None
        assert mock_test_case.tearDown is None
        assert mock_test_case.testMethodName is None
    else:
        assert mock_test_case.setUp() == "setup_skipped"
        assert (
            mock_test_case.testMethodName()
            == "skipped due to non-matching variant value"
        )
        assert mock_test_case.tearDown() == "tearDown_skipped"


def test_test_execution_apply_tc_name_filter(mocker):
    mock_test_case = mocker.Mock()
    mock_test_case.setUp = None
    mock_test_case.tearDown = None
    mock_test_case.testMethodName = None
    mock_test_case.skipTest = lambda x: x  # return input
    mock_test_case.tag = None
    mock_test_case._testMethodName = "testMethodName"
    mock_test_case.__class__.__name__ = "testClass1"

    test_cases = []
    for id in range(10):
        mock_test_case._testMethodName = f"test_run_{id}"
        test_cases.append(copy.deepcopy(mock_test_case))

    mock = mocker.patch(
        "pykiso.test_coordinator.test_execution.test_suite.flatten",
        return_value=test_cases,
    )

    new_testsuite = test_execution.apply_test_case_filter(
        {}, "testClass1", "test_run_[2-5]"
    )
    assert len(new_testsuite._tests) == 4
    assert new_testsuite._tests[0]._testMethodName == "test_run_2"
    assert new_testsuite._tests[1]._testMethodName == "test_run_3"
    assert new_testsuite._tests[2]._testMethodName == "test_run_4"
    assert new_testsuite._tests[3]._testMethodName == "test_run_5"

    new_testsuite = test_execution.apply_test_case_filter({}, "testClass1", None)
    assert len(new_testsuite._tests) == 10

    new_testsuite = test_execution.apply_test_case_filter(
        {}, "NotExistingTestClass", None
    )
    assert len(new_testsuite._tests) == 0


@pytest.mark.parametrize("tmp_test", [("step_aux1", "step_aux2", False)], indirect=True)
def test_config_registry_and_test_execution_with_step_report(tmp_test, capsys):
    """Call execute function from test_execution using
    configuration data coming from parse_config method

    Validation criteria:
        -  creates step report file
    """
    cfg = parse_config(tmp_test)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, step_report="step_report.html")
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "RUNNING TEST: " in output.err
    assert "END OF TEST: " in output.err
    assert "->  Passed" in output.err
    assert pathlib.Path("step_report.html").is_file()
