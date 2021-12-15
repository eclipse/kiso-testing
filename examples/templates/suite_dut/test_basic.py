##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test-App : Basic test implementation
************************************

:module: test_basic

:synopsis: show how to implement Test-App style basic tests. In In this
    module, we will be focused on DUTAuxiliary capability and usage.

A complete test suite run is represented by the following call sequence:

|--> test suite setup
    |
    ------> test case 1 setup
    |
    ------> test case 1 run
    |
    ------> test case 1 teardown
    |
    .
    .
    .
    |
    ------> test case n setup
    |
    ------> test case n run
    |
    ------> test case n teardown
    |
|--> test suite teardown

And depending on the fixture type and nature the following parameters
are usable :

- suite_id : current test suite identification number
- case_id : current test case identification number
- aux_list : a list of auxiliary's alias to use for this fixture
- setup_timeout [optional]: timeout applies on report waiting phase for
setup fixture
- run_timeout [optional]: timeout applies on report waiting phase for
run fixture
- teardown_timeout [optional]:timeout applies on report waiting phase
for teardown fixture
- test_ids [optional]: dictionary of covered requirement ids

Finally, if one of the above fixture is not overridden, behind the
scene, a default Test-App sequence is applied between Test Manager (TM)
and Device Under Test (DUT). This particular sequence is described
below :

       TM |   COMMAND      ---------->                | DUT
       TM |                <----------  ACK           | DUT
       TM |                <----------  LOG[optional] | DUT
       TM | ACK[optional]  ---------->                | DUT
       ...
       TM |                <----------  LOG[optional] | DUT
       TM | ACK[optional]  ---------->                | DUT
       TM |                <---------- REPORT         | DUT
       TM |   ACK          ---------->                | DUT


.. currentmodule:: test_basic
"""

import logging

import pykiso
from pykiso.auxiliaries import aux1, aux2


# Add test suite setup fixture, run once at test suite's beginning.
@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], setup_timeout=2)
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    """This test suite setup will be executed using base behavior
    given by BasicTestSuiteSetup class and test_suite_setUp method.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite setup :

    -> suite_id : suite id set to 1
    -> aux_list : test suite setup will be executed for aux1 and aux2
    -> setup_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.

    If setup_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


# Add test suite teardown fixture, run once at test suite's end.
@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], teardown_timeout=2)
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    """This test suite setup will be executed using base behavior
    given by BasicTestSuiteTeardown class and test_suite_tearDown
    method.

    Using decorator define_test_parameters the following parameters will
    be applied on test suite setup :

    -> suite_id : suite id set to 1
    -> aux_list : test suite teardown will be executed for aux1 and aux2
    -> teardown_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.

    If teardown_timeout is not given the default timeout value is 10
    seconds.
    """

    pass


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[aux1, aux2],
    setup_timeout=1,
    run_timeout=2,
    teardown_timeout=1,
    test_ids={"Component1": ["Req-01"]},
    variant=["variant1"],
)
class TestCaseBasic(pykiso.BasicTest):
    """This test case definition will be executed using base behavior
    given by BasicTest class and setUp, test_run, tearDown methods

    Using decorator define_test_parameters the following parameters will
    be applied on test case setUp, test_run and tearDown:

    -> suite_id : suite id set to 1
    -> case_id : case id set to 1
    -> aux_list : test case test_run, setUp, and tearDown will be
    executed using aux1, aux2
    -> setup_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> run_timeout : ITF will wait 2 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> teardown_timeout : ITF will wait 1 seconds (maximum) to receive a
    report from device under test otherwise an abort command is sent.
    -> test_ids: indicates the covered requirement

    If setup_timeout, run_timeout and teardown_timeout are not given the
    default timeout value is 10 seconds for each.
    """

    pass
