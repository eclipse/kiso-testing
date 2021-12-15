##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
test_suite_2
************

:module: test_suite_2

:synopsis: Basic example on how to write and configure test suite and
case on ITF side in order to communicate with the device under test
using TestApp.
"""


import pykiso
from pykiso.auxiliaries import aux1, aux2


@pykiso.define_test_parameters(suite_id=2, case_id=0, aux_list=[aux1, aux2])
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    """This test suite setup will be executed using base behavior given
    by BasicTestSuiteTeardown.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite setup :

    -> suite_id : set to 2
    -> case_id : not mandatory for test suite setup default value is 0.
    In addition for test suite fixture this parameter is not take into
    account.
    -> aux_list : test suite setup executed using aux1 and aux2 (see
    yaml configuration file)

    If setup_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


@pykiso.define_test_parameters(suite_id=2, case_id=0, aux_list=[aux1, aux2])
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    """This test suite teardown will be executed using base behavior
    given by BasicTestSuiteTeardown.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite teardown :

    -> suite_id : set to 2
    -> case_id : not mandatory for test suite teardown default value is
    0. In addition for test suite fixture this parameter is not take
    into account.
    -> aux_list : test suite teardown executed using aux1 and aux2 (see
    yaml configuration file)
    -> teardown_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.

    If teardown_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


@pykiso.define_test_parameters(
    suite_id=2,
    case_id=1,
    aux_list=[aux1],
    setup_timeout=5,
    run_timeout=2,
    teardown_timeout=3,
    variant={"variant": ["variant3", "variant2"], "branch_level": ["daily"]},
)
class MyTest4(pykiso.BasicTest):
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


@pykiso.define_test_parameters(suite_id=2, case_id=2, aux_list=[aux2])
class MyTest2(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by BasicTest.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : set to 2
    -> case_id : set to 2
    -> aux_list : test case executed using aux2(see yaml
    configuration file)

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    pass
