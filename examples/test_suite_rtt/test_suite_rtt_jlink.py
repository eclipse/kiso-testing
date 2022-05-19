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
from pykiso.auxiliaries import aux1


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1])
class TestSuiteSetUp(pykiso.GreyTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[aux1])
class TestCase(pykiso.GreyTest):
    pass


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1])
class TestSuiteTearDown(pykiso.GreyTestSuiteTeardown):
    pass
