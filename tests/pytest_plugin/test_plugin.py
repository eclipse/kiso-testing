##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pytest
from _pytest.pytester import Pytester
from pytest import CaptureFixture


@pytest.mark.slow
def test_run_pykiso_testsuite(pytester: Pytester, dummy_pykiso_testsuite):
    result = pytester.runpytest(dummy_pykiso_testsuite)

    result.assert_outcomes(passed=4)


@pytest.mark.slow
def test_run_pykiso_testsuite_with_tags(pytester: Pytester, dummy_pykiso_testsuite):
    result = pytester.runpytest(dummy_pykiso_testsuite, "--tags", "variant=var1")

    result.assert_outcomes(passed=2, skipped=2)


@pytest.mark.slow
def test_run_pytest_testsuite(
    pytester: Pytester, tmp_path, capsys: CaptureFixture, dummy_pytest_testsuite
):
    result = pytester.runpytest(
        dummy_pytest_testsuite,
        "--log-level=INFO",
        "--log-cli-level=INFO",
        "--log-file-level=INFO",
        f"--log-file={tmp_path}/test_pytest_plugin/tmp.log",
        "-vv",
    )

    # verify internal logging configuration
    with open(f"{tmp_path}/test_pytest_plugin/tmp.log") as log_file:
        assert "INTERNAL_INFO" in log_file.read()

    assert "INTERNAL_INFO" in capsys.readouterr().out

    result.assert_outcomes(passed=2)


@pytest.mark.slow
def test_run_pytest_testsuite_with_tags(pytester: Pytester, dummy_pytest_testsuite):
    result = pytester.runpytest(dummy_pytest_testsuite, "--tags", "variant=var1")

    result.assert_outcomes(passed=1, skipped=1)
