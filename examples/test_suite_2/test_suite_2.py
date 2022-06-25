##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
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


@pykiso.define_test_parameters(suite_id=2, aux_list=[aux1, aux2])
class SuiteSetup(pykiso.RemoteTestSuiteSetup):
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
    """


@pykiso.define_test_parameters(suite_id=2, aux_list=[aux1, aux2])
class SuiteTearDown(pykiso.RemoteTestSuiteTeardown):
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
    """


@pykiso.define_test_parameters(
    suite_id=2,
    case_id=1,
    aux_list=[aux1],
    tag={"variant": ["variant3", "variant2"], "branch_level": ["daily"]},
)
class MyTest4(pykiso.RemoteTest):
    """This test case definition will be executed using base behavior
    given by BasicTest.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : set to 1
    -> case_id : set to 3
    -> aux_list : test case test_run, setUp, and tearDown executed using
    aux1(see yaml configuration file)
    -> test_ids: [optional] store the requirements into the report
    -> tag: [optional] allows the run of subset of tests
    """


@pykiso.define_test_parameters(suite_id=2, case_id=2, aux_list=[aux2])
class MyTest5(pykiso.RemoteTest):
    """This test case definition will be executed using base behavior
    given by BasicTest.

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : set to 2
    -> case_id : set to 2
    -> aux_list : test case executed using aux2(see yaml
    configuration file)
    """
