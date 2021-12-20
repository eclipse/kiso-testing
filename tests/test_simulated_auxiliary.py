##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import re
import sys
import unittest
from pathlib import Path

import pytest

from pykiso import cli
from pykiso.test_coordinator import test_execution
from pykiso.test_setup.config_registry import ConfigRegistry

expected_failures = [
    (
        "test_suite_setUp",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_setUp",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:21, type:2, error_code:0, reserved:0, test_suite ID:4, test_case ID:0!",
    ),
    (
        "test_suite_setUp",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:28, type:2, error_code:0, reserved:0, test_suite ID:5, test_case ID:0!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:71, type:3, error_code:0, reserved:0, test_suite ID:1, test_case ID:4!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:78, type:3, error_code:0, reserved:0, test_suite ID:1, test_case ID:5!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:145, type:13, error_code:0, reserved:0, test_suite ID:1, test_case ID:8!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:168, type:13, error_code:0, reserved:0, test_suite ID:1, test_case ID:9!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:251, type:23, error_code:0, reserved:0, test_suite ID:1, test_case ID:12!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:18, type:23, error_code:0, reserved:0, test_suite ID:1, test_case ID:13!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_tearDown",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_tearDown",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:69, type:22, error_code:0, reserved:0, test_suite ID:8, test_case ID:0!",
    ),
    (
        "test_suite_tearDown",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:76, type:22, error_code:0, reserved:0, test_suite ID:9, test_case ID:0!',)",
    ),
]


@pytest.fixture
def prepare_config():
    """return the configuration file path virtual.yaml"""
    project_folder = Path.cwd()
    config_file_path = project_folder / "examples/virtual.yaml"
    return config_file_path


@pytest.mark.slow
def test_virtual_cfg_output(capsys, prepare_config):
    """run the 'virtual.yaml' configuration and compare it to
    expected outputs.

    The outputs are pre-generated and we just ensure that they don't
    change arbitrarily.
    """
    cfg = cli.parse_config(prepare_config)
    with pytest.raises(SystemExit):
        config_registry = ConfigRegistry(cfg)
        config_registry.register_aux_con()
        exit_code = test_execution.execute(cfg)
        config_registry.delete_aux_con()
        sys.exit(exit_code)

    output = capsys.readouterr()
    assert "F.FFF.FFF.FFF.FF..FF.FF" in output.err
    pattern = r"=+\s+FAIL: (\w+)\s+.*?AssertionError: ([^\n]+)$"
    failures = [
        m.groups() for m in re.finditer(pattern, output.err, re.MULTILINE + re.DOTALL)
    ]

    drop_aux_pattern = re.compile(r"auxiliairy : <.*?>")
    drop_token_pattern = re.compile(r"message_token:\d+")

    for (res_place, res_err), (ex_place, ex_err) in zip(failures, expected_failures):
        assert res_place == ex_place
        # remove aux field as that contains information that changes from run to run
        actual_error = drop_aux_pattern.sub("auxiliary : REMOVED", res_err)
        actual_error = drop_token_pattern.sub("message_toke:REMOVED", actual_error)
        expected_error = drop_aux_pattern.sub("auxiliary : REMOVED", ex_err)
        expected_error = drop_token_pattern.sub("message_toke:REMOVED", expected_error)
        assert actual_error == expected_error
