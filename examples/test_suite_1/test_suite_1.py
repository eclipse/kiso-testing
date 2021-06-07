##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
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

import pykiso
from pykiso.auxiliaries import aux1, aux2, aux3


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
)
class MyTest(pykiso.BasicTest):
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

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    def test_run(self):
        """In this case the default test_run method is overridden and
        instead of calling test_run from BasicTest class the following
        code is call.
        """
        logging.info("I HAVE RUN 0.1.1!")


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=2,
    aux_list=[aux2, aux3],
    setup_timeout=1,
    run_timeout=2,
    teardown_timeout=1,
    test_ids={"Component1": ["Req"]},
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

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    def test_run(self):
        """In this case the default test_run method is called using the
        python syntax super(), in addition aux3, aux2 running is paused
        and resumed.
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
    aux_list=[aux1],
    setup_timeout=5,
    run_timeout=2,
    teardown_timeout=3,
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

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    pass
