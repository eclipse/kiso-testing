##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
test_suite_1
************

:module: test_suite_1

:synopsis: Basic example on how to write and configure test suite and
case on ITF side in order to communicate with the device under test
using TestApp.
"""

import logging
from itertools import cycle

import pykiso
from pykiso.auxiliaries import aux1, aux2, aux3

# define an external iterator that can be used for retry_test_case demo
side_effect = cycle([False, False, True])


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], setup_timeout=2)
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    """This test suite setup will be executed using base behavior
    given by BasicTestSuiteTeardown.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite setup :

    -> suite_id : set to 1
    -> aux_list : test suite setup executed using aux1 and aux2 (see
    yaml configuration file)
    -> setup_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.

    If setup_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], teardown_timeout=2)
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    """This test suite teardown will be executed using base behavior
    given by BasicTestSuiteTeardown.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite teardown :

    -> suite_id : set to 1
    -> aux_list : test suite teardown executed using aux1 and aux2 (see
    yaml configuration file)
    -> teardown_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.

    If teardown_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[aux1],
    setup_timeout=1,
    teardown_timeout=1,
    test_ids={"Component1": ["Req1", "Req2"], "Component2": ["Req3"]},
    variant={"variant": ["variant2", "variant1"], "branch_level": ["daily", "nightly"]},
)
class MyTest1(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by BasicTest only for setUp and tearDown method.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp and tearDown:

    -> suite_id : set to 1
    -> case_id : set to 1
    -> aux_list : test case test_run, setUp, and tearDown executed using
    aux1 (see yaml configuration file)
    -> setup_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> teardown_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> test_ids: [optional] store the requirements into the report
    -> variant: [optional] allows the run of subset of tests

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    @pykiso.retry_test_case(max_try=3)
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run.
        In this case the default setUp method is overridden, allowing us to apply the
        retry_test_case's decorator. The syntax super() access to the BasicTest and
        we will run the default setUp()
        """
        super().setUp()

    @pykiso.retry_test_case(max_try=5, rerun_setup=True, rerun_teardown=True)
    def test_run(self):
        """In this case the default test_run method is overridden and
        instead of calling test_run from BasicTest class the following
        code is called.

        Here, the test pass at the 3rd attempt out of 5. The setup and
        tearDown methods are called for each attempt.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        self.assertTrue(next(side_effect), "Retry demo")
        logging.info(f"I HAVE RUN 0.1.1 for variant {self.variant}!")

    @pykiso.retry_test_case(max_try=3)
    def tearDown(self):
        """Hook method from unittest in order to execute code after the test case ran.
        In this case the default tearDown method is overridden, allowing us to apply the
        retry_test_case's decorator. The syntax super() access to the BasicTest and
        we will run the default tearDown()
        """
        super().tearDown()


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=2,
    aux_list=[aux2, aux3],
    setup_timeout=1,
    run_timeout=2,
    teardown_timeout=1,
    test_ids={"Component1": ["Req"]},
    variant={"branch_level": ["nightly"]},
)
class MyTest2(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by BasicTest.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : set to 1
    -> case_id : set to 2
    -> aux_list : test case test_run, setUp, and tearDown executed using
    aux2, aux3 (see yaml configuration file)
    -> setup_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> run_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> teardown_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> test_ids: [optional] store the requirements into the report
    -> variant: [optional] allows the run of subset of tests

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """
    @pykiso.retry_test_case(
        max_try=1, rerun_setup=False, rerun_teardown=False, stability_test=True
    )
    def test_run(self):
        """In this case the default test_run method is called using the
        python syntax super(), in addition aux3, aux2 running is paused
        and resumed.

        This test will be run 3 times in order to test stability (setUp
        and tearDown excluded as the flags are set to False).
        """
        logging.info(f"------------suspend auxiliaries run-------------")
        aux3.suspend()
        aux2.suspend()
        logging.info(f"------------resume auxiliaries run--------------")
        aux3.resume()
        aux2.resume()
        super().test_run()
        logging.info("I HAVE RUN 0.1.2!")


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=3,
    aux_list=[aux1, aux3],
    setup_timeout=5,
    run_timeout=2,
    teardown_timeout=3,
    variant={"variant": ["variant3"]},
)
class MyTest3(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by BasicTest.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : set to 1
    -> case_id : set to 3
    -> aux_list : test case test_run, setUp, and tearDown executed using
    aux1(see yaml configuration file)
    -> setup_timeout : ITF will wait 5 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> run_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> teardown_timeout : ITF will wait 3 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> test_ids: [optional] store the requirements into the report
    -> variant: [optional] allows the run of subset of tests

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    pass


@pykiso.define_test_parameters(suite_id=1, case_id=4, aux_list=[aux1])
class MyTest4(pykiso.BasicTest):
    """This test is used for the step report example.

    To generate it, add --junit --step-report flags:
        pykiso -c ./examples/dummy.yaml --junit --step-report
    """

    def setUp(self):
        """Hook method from unittest in order to execute code before test
        case run. In this case the default setUp method is overridden.
        """
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        device_on = True
        self.step_report_message = "smth"
        self.step_report_continue_on_error = True
        self.assertTrue(device_on, msg="Check my device is ready")
        voltage = 3.8
        self.assertAlmostEqual(voltage, 4, delta=1, msg="err")
        # additional data can be shown in the step-report
    

    def test_run(self):
        """Here is my test description which will be showed in the step-report"""
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        kiso_is_great = True
        self.step_report_continue_on_error = True
        self.assertTrue(False, "Some verification")
        wrong_placement = "123"
        self.assertEqual(
            "123",
            wrong_placement,
            "Variable name not found because data_in/data_expected order inverted",
        )
        logging.info(f"I HAVE RUN 0.1.1 for variant {self.variant}!")

    def tearDown(self):
        """Hook method from unittest in order to execute code after the test case ran.
        In this case the default tearDown method is overridden.
        """
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        teardown_has_started = True
        self.assertTrue(teardown_has_started, "Another Example")
