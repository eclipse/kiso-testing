##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pykiso
from pykiso.auxiliaries import zephyr_aux
from pykiso.lib.auxiliaries.zephyr import TestResult


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[zephyr_aux],
)
class MyTest1(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by RemoteTest only for setUp and tearDown method.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp and tearDown:

    -> suite_id : set to 1
    -> case_id : set to 1
    -> aux_list : test case test_run, setUp, and tearDown executed using
    aux1 (see yaml configuration file)
    -> test_ids: [optional] store the requirements into the report
    -> tag: [optional] allows the run of subset of tests
    """

    def test_run(self):
        """In this case the default test_run method is overridden and
        instead of calling test_run from RemoteTest class the following
        code is called.



        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # This starts the test on the target and returns as soon as the test is running.
        # If an error occurs, it will raise an exception and finish the test.
        zephyr_aux.start_test()
        logging.info(f"Zephyr test is running")

        # Interact with the running device under test if needed...

        # Wait for Zephyr test to finish and collect test result from the target.
        # If an error occurs, it will raise an exception and finish the test.
        result: TestResult = zephyr_aux.wait_test()
        logging.info(f"Zephyr test has finished: {result}")
        # The test case can decide how to handle test results from device under test.
        self.assertEqual(result, TestResult.PASSED)
