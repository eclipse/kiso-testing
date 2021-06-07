##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys
import unittest

import pytest

from pykiso import cli
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

        runner = unittest.TextTestRunner()
        result = runner.run(self.init.suite)
        self.init.stop()

        self.assertEqual(result.wasSuccessful(), True)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, len(parameters))


@pytest.mark.parametrize(
    "suite_id, case_id, aux_list, setup_timeout, run_timeout, teardown_timeout, test_ids",
    [
        (1, 1, None, 1, 2, 3, {"Component1": ["Req1", "Req2"]}),
        (1, 2, ["aux2"], None, 2, 3, {"Component1": ["Req1", "Req2"]}),
        (1, 3, ["aux3"], 1, None, 3, {"Component1": ["Req1", "Req2"]}),
        (1, 4, ["aux4"], 1, 2, None, {"Component1": ["Req1", "Req2"]}),
        (1, 5, ["aux5", "aux6"], None, None, None, {"Component1": ["Req1", "Req2"]}),
        (
            1,
            5,
            ["aux5", "aux6"],
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_define_test_parameters_on_tc(
    suite_id, case_id, aux_list, setup_timeout, run_timeout, teardown_timeout, test_ids
):
    @test_case.define_test_parameters(
        suite_id=suite_id,
        case_id=case_id,
        aux_list=aux_list,
        setup_timeout=setup_timeout,
        run_timeout=run_timeout,
        teardown_timeout=teardown_timeout,
        test_ids=test_ids,
    )
    class MyClass(test_case.BasicTest):
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


def test_setUpClass(mocker):
    mocker.patch.object(
        test_case,
        "get_logging_options",
        return_value=cli.LogOptions(None, "ERROR", "junit"),
    )
    mock_init_log = mocker.patch.object(test_case, "initialize_logging")
    test_case.BasicTest.setUpClass()
    mock_init_log.assert_called_with(None, "ERROR", "junit")
