##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
:module: utils

:synopsis: implements common utilities to support the pytest-pykiso duality.
"""

from __future__ import annotations

import sys
import unittest
from typing import Callable, TypeVar

from _pytest.unittest import TestCaseFunction

from pykiso.test_coordinator.test_case import BasicTest
from pykiso.test_coordinator.test_suite import BaseTestSuite

T = TypeVar("T", bound=Callable)


def export(func: T) -> T:
    """Decorator to add a function or a class to its module's ``__all__``."""
    mod = sys.modules[func.__module__]
    if hasattr(mod, "__all__"):
        mod.__all__.append(func.__name__)
    else:
        mod.__all__ = [func.__name__]
    return func


export(export)


@export
def get_base_testcase(item: TestCaseFunction) -> unittest.TestCase:
    """Returns the unittest test case wrapped within a pytest test case.

    :param item: pytest-collected test case.
    :return: wrapped unittest test case (or pykiso test case).
    """
    return item.parent._obj(item.name)


@export
def is_kiso_testcase(tc):
    """
    Determine whether the provided test case is a pykiso test case
    wrapped by pytest.
    """
    return isinstance(tc, TestCaseFunction) and isinstance(get_base_testcase(tc), (BasicTest, BaseTestSuite))
