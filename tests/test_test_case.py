##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import unittest
from functools import partial

import pytest

from pykiso import cli, retry_test_case
from pykiso.logging_initializer import LogOptions
from pykiso.test_coordinator import test_case


@pytest.mark.usefixtures("CustomTestCaseAndSuite")
class IntegrationTestCase(unittest.TestCase):
    def test_load_test_case(self):
        """run a default test case (see conftest.py), using existing auxiliaries
        (ExampleAuxiliary) and connectors (CCExample)

        Validation criteria:
        -  sub class from test_case.BasicTest behave like unittest.TestCase
        -  all test are PASSED
        -  no error are reported
        -  no failure is reported
        -  no test case are skipped
        -  number of test run equal to len of parameters set
        """
        self.init.create_communication_pipeline(3)
        parameters = [
            (1, 1, self.init.auxiliaries),
            (1, 2, [self.init.auxiliaries[0]]),
            (2, 3, [self.init.auxiliaries[1]]),
            (1, 4, [self.init.auxiliaries[2]]),
            (0, 5, self.init.auxiliaries[0:2]),
        ]

        for params in parameters:
            self.init.prepare_default_test_cases(params)
            self.init.prepare_remote_test_cases(params)

        runner = unittest.TextTestRunner()
        result = runner.run(self.init.suite)
        self.init.stop()

        self.assertEqual(result.wasSuccessful(), True)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, len(parameters * 2))


@pytest.mark.parametrize(
    "suite_id, case_id, aux_list, test_ids, tag, setup_timeout",
    [
        (
            1,
            1,
            None,
            {"Component1": ["Req1", "Req2"]},
            None,
            None,
        ),
        (
            1,
            2,
            ["aux2"],
            {"Component1": ["Req1", "Req2"]},
            None,
            None,
        ),
        (
            1,
            3,
            ["aux3"],
            {"Component1": ["Req1", "Req2"]},
            None,
            None,
        ),
        (
            1,
            4,
            ["aux4"],
            {"Component1": ["Req1", "Req2"]},
            None,
            None,
        ),
        (
            1,
            5,
            ["aux5", "aux6"],
            {"Component1": ["Req1", "Req2"]},
            None,
            5,
        ),
        (1, 5, ["aux1"], None, None, None),
        (1, 5, ["aux1"], {"Component1": ["Req1"]}, {"variant": ["variant1"]}, 10),
    ],
)
def test_define_test_parameters_on_basic_tc(
    suite_id,
    case_id,
    aux_list,
    test_ids,
    tag,
    setup_timeout,
    caplog,
):
    @test_case.define_test_parameters(
        suite_id=suite_id,
        case_id=case_id,
        aux_list=aux_list,
        test_ids=test_ids,
        tag=tag,
        setup_timeout=setup_timeout,
    )
    class MyClass(test_case.BasicTest):
        pass

    tc_inst = MyClass()
    assert tc_inst.test_suite_id == suite_id
    assert tc_inst.test_case_id == case_id
    aux_list = aux_list or []
    assert tc_inst.test_auxiliary_list == aux_list

    if setup_timeout is not None:
        with caplog.at_level(logging.WARNING):
            assert (
                "BasicTest does not support test timeouts, it will be discarded"
                in caplog.text
            )

    assert tc_inst.test_ids == test_ids
    assert tc_inst.tag == tag


@pytest.mark.parametrize(
    "suite_id, case_id, aux_list, setup_timeout, run_timeout, teardown_timeout, test_ids, tag",
    [
        (1, 1, None, 1, 2, 3, {"Component1": ["Req1", "Req2"]}, None),
        (1, 2, ["aux2"], None, 2, 3, {"Component1": ["Req1", "Req2"]}, None),
        (1, 3, ["aux3"], 1, None, 3, {"Component1": ["Req1", "Req2"]}, None),
        (1, 4, ["aux4"], 1, 2, None, {"Component1": ["Req1", "Req2"]}, None),
        (
            1,
            5,
            ["aux5", "aux6"],
            None,
            None,
            None,
            {"Component1": ["Req1", "Req2"]},
            None,
        ),
        (1, 5, ["aux1"], None, None, None, None, None),
        (
            1,
            5,
            ["aux1"],
            1,
            2,
            3,
            {"Component1": ["Req1"]},
            {"variant": ["variant1"]},
        ),
    ],
)
def test_define_test_parameters_on_remote_tc(
    suite_id,
    case_id,
    aux_list,
    setup_timeout,
    run_timeout,
    teardown_timeout,
    test_ids,
    tag,
):
    @test_case.define_test_parameters(
        suite_id=suite_id,
        case_id=case_id,
        aux_list=aux_list,
        setup_timeout=setup_timeout,
        run_timeout=run_timeout,
        teardown_timeout=teardown_timeout,
        test_ids=test_ids,
        tag=tag,
    )
    class MyClass(test_case.RemoteTest):
        pass

    tc_inst = MyClass()
    assert tc_inst.test_suite_id == suite_id
    assert tc_inst.test_case_id == case_id
    aux_list = aux_list or []
    assert tc_inst.test_auxiliary_list == aux_list

    timeout_value = setup_timeout or tc_inst.response_timeout
    assert tc_inst.setup_timeout == timeout_value
    timeout_value = run_timeout or tc_inst.response_timeout
    assert tc_inst.run_timeout == timeout_value
    timeout_value = teardown_timeout or tc_inst.response_timeout
    assert tc_inst.teardown_timeout == timeout_value
    assert tc_inst.test_ids == test_ids
    assert tc_inst.tag == tag


def test_setUpClass(mocker):
    mocker.patch.object(
        test_case,
        "get_logging_options",
        return_value=LogOptions(None, "ERROR", "junit", False),
    )
    mock_init_log = mocker.patch.object(test_case, "initialize_logging")
    test_case.BasicTest.setUpClass()
    mock_init_log.assert_called_with(None, "ERROR", False, "junit")

    test_case.RemoteTest.setUpClass()
    mock_init_log.assert_called_with(None, "ERROR", False, "junit")


@pytest.mark.parametrize(
    "max_try, rerun_setup, rerun_teardown, stability_test, expected_exception, expected_run_count, expected_setup_count, expected_teardown_count",
    [
        (
            5,
            True,
            True,
            False,
            None,
            3,
            2,
            2,
        ),
        (
            3,
            True,
            True,
            False,
            None,
            3,
            2,
            2,
        ),
        (
            3,
            True,
            False,
            False,
            None,
            3,
            2,
            0,
        ),
        (
            3,
            False,
            False,
            False,
            None,
            3,
            0,
            0,
        ),
        (
            2,
            True,
            True,
            False,
            Exception,
            2,
            1,
            1,
        ),
        (
            2,
            True,
            False,
            False,
            Exception,
            2,
            1,
            0,
        ),
        (
            5,
            True,
            True,
            True,
            None,
            5,
            4,
            4,
        ),
        (
            10,
            True,
            True,
            True,
            Exception,
            6,
            5,
            5,
        ),
    ],
)
def test_retry_on_failure_decorator(
    max_try,
    rerun_setup,
    rerun_teardown,
    stability_test,
    expected_exception,
    expected_run_count,
    expected_setup_count,
    expected_teardown_count,
    mocker,
    caplog,
):
    mock_test_case_class = mocker.Mock()

    if not stability_test:
        mock_test_case_class.test_run.side_effect = [
            Exception("try again"),
            Exception("try harder"),
            "bingo",
        ]
    else:
        mock_test_case_class.test_run.side_effect = list(range(5)) + [
            Exception("Exception")
        ]
    # fix __name__ for the mock.test_run
    mock_test_case_class.test_run.__name__ = "test_run"

    partial_test_run = partial(
        retry_test_case(max_try, rerun_setup, rerun_teardown, stability_test)(
            mock_test_case_class.test_run
        )
    )
    if expected_exception:
        with pytest.raises(expected_exception):
            assert partial_test_run(mock_test_case_class)
            assert "Mock.test_run failed with exception: try again" in caplog.text
    else:
        partial_test_run(mock_test_case_class)

    assert mock_test_case_class.setUp.call_count == expected_setup_count
    assert mock_test_case_class.test_run.call_count == expected_run_count
    assert mock_test_case_class.tearDown.call_count == expected_teardown_count
