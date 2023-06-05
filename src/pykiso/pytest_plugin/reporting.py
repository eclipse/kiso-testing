##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Report customization
********************

:module: reporting

:synopsis: customize the generated reports with pykiso-specific properties.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import *

if TYPE_CHECKING:
    from _pytest.nodes import Item
    from _pytest.runner import CallInfo

    from pykiso.test_coordinator.test_case import BasicTest


@export
def pytest_runtest_makereport(item: Item, call: CallInfo[None]) -> None:
    """Add the test IDs to the JUnit report to the user properties in order to add
    them to the generated reports.

    :param item: collected test item.
    :param call: the result of the test item's execution.
    """
    if call.when != "setup":
        return

    if is_kiso_testcase(item):
        kiso_tc: BasicTest = get_base_testcase(item)
        test_ids = kiso_tc.test_ids
    else:
        test_ids_marker = item.get_closest_marker("test_ids", default=None)
        test_ids = test_ids_marker.kwargs if test_ids_marker is not None else None

    item.user_properties.append(("test_ids", test_ids))
