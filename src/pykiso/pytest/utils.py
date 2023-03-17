##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Common utilities
****************

:module: utils

:synopsis: implements common utilities to support the pytest-pykiso duality.

.. currentmodule:: utils

"""

from __future__ import annotations

import unittest

from _pytest.unittest import TestCaseFunction

from pykiso.test_coordinator.test_case import BasicTest
from pykiso.test_coordinator.test_suite import BaseTestSuite


def get_base_testcase(item: TestCaseFunction) -> unittest.TestCase:
    return item.parent._obj(item.name)


def is_kiso_testcase(tc):
    return isinstance(tc, TestCaseFunction) and isinstance(
        get_base_testcase(tc), (BasicTest, BaseTestSuite)
    )
