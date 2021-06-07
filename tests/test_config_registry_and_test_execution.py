##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import itertools
import sys
from unittest import TestCase, TestResult

import pytest

from pykiso import cli
from pykiso.config_parser import parse_config
from pykiso.test_coordinator import test_execution
from pykiso.test_setup.config_registry import ConfigRegistry

AUX_NAMES = itertools.cycle(
    [
        ("aux1", "aux2"),
        ("text_aux1", "text_aux2"),
        ("juint_aux1", "juint_aux2"),
    ]
)

TestResult.__test__ = False


@pytest.fixture
def tmp_cfg(tmp_path):
    cli.log_options = cli.LogOptions(None, "ERROR", None)

    aux1, aux2 = next(AUX_NAMES)
    ts_folder = tmp_path / f"test_suite_{aux1}_{aux2}"
    ts_folder.mkdir()
    tc_file = ts_folder / f"test_{aux1}_{aux2}.py"
    tc_content = create_test_case(aux1, aux2)
    tc_file.write_text(tc_content)

    config_file = tmp_path / f"{aux1}_{aux2}.yaml"
    cfg_content = create_config(aux1, aux2, f"test_suite_{aux1}_{aux2}")
    config_file.write_text(cfg_content)

    return config_file


def create_config(aux1, aux2, suite_dir):
    cfg = (
        """auxiliaries:
  """
        + aux1
        + """:
    connectors:
        com: chan1
    config: null
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
  """
        + aux2
        + """:
    connectors:
        com:   chan2
        flash: chan3
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
connectors:
  chan1:
    config: null
    type: pykiso.lib.connectors.cc_example:CCExample
  chan2:
    type: pykiso.lib.connectors.cc_example:CCExample
  chan3:
    config:
        configKey: "config value"
    type: pykiso.lib.connectors.cc_example:CCExample
test_suite_list:
- suite_dir: """
        + suite_dir
        + """
  test_filter_pattern: '*.py'
  test_suite_id: 1
    """
    )
    return cfg


def create_test_case(aux1, aux2):
    tc = (
        """
import pykiso
import logging

from pykiso.auxiliaries import """
        + aux1
        + """, """
        + aux2
        + """


@pykiso.define_test_parameters(suite_id=1, aux_list=["""
        + aux1
        + ","
        + aux2
        + """])
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=1, aux_list=["""
        + aux1
        + ","
        + aux2
        + """])
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=["""
        + aux1
        + """])
class MyTest(pykiso.BasicTest):
    def test_run(self):
        logging.info("I HAVE RUN 0.1.1!")


@pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=["""
        + aux2
        + """])
class MyTest2(pykiso.BasicTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=3, aux_list=["""
        + aux1
        + """])
class MyTest3(pykiso.BasicTest):
    pass
    """
    )
    return tc


def test_config_registry_and_test_execution(tmp_cfg, capsys):
    """Call run method from test_factory_and_execution using
    configuration data coming from parse_config method

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_cfg)
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err


def test_config_registry_and_test_execution_with_text_reporting(tmp_cfg, capsys):
    """Call run method from test_factory_and_execution using
    configuration data coming from parse_config method and
    --text option to show the test results only in console

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_cfg)
    report_option = "text"
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, report_option)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err


def test_config_registry_and_test_execution_with_junit_reporting(tmp_cfg, capsys):
    """Call run method from test_factory_and_execution using
    configuration data coming from parse_config method and
    --junit option to show the test results in console
    and to generate a junit xml report

    Validation criteria:
        -  run is executed without error
    """
    cfg = parse_config(tmp_cfg)
    report_option = "junit"
    ConfigRegistry.register_aux_con(cfg)
    exit_code = test_execution.execute(cfg, report_option)
    ConfigRegistry.delete_aux_con()

    output = capsys.readouterr()
    assert "FAIL" not in output.err


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
