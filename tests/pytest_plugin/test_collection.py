##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys

import pytest
from _pytest.pytester import Pytester

from pykiso.test_result.text_result import ResultStream
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture
def setup():
    """Necessary to restore the changes from the previous tests."""
    ConfigRegistry._linker = None
    if isinstance(sys.stderr, ResultStream):
        sys.stderr.close()
    yield


@pytest.mark.parametrize(
    "fixture_name",
    ["dummy_multiple_testsuites", "dummy_mixed_testsuite"],
    ids=[
        "one pykiso suite - one pytest suite",
        "a single mixed pykiso and pytest suite",
    ],
)
def test_multiple_testsuites(setup, pytester: Pytester, request, fixture_name):
    cfg_name = request.getfixturevalue(fixture_name)
    hook_recorder = pytester.inline_run(str(cfg_name), "--collectonly")

    collected_items = [x.item for x in hook_recorder.getcalls("pytest_itemcollected")]
    sorted_items = [
        x.items for x in hook_recorder.getcalls("pytest_collection_modifyitems")
    ][0]

    for hookcall in hook_recorder.getcalls("pytest_collection_modifyitems"):
        sorted_items = hookcall.items
        if sorted_items == collected_items:
            continue

    assert len(collected_items) == len(sorted_items)
    assert collected_items != sorted_items

    sorted_item_names = [item.originalname for item in sorted_items]
    assert sorted_item_names == [
        "test_suite_setUp",
        "test_run1",
        "test_run",
        "test_suite_tearDown",
        "test_mytest1",
        "test_mytest2",
    ]


def test_fails_no_matching_tag(setup, pytester: Pytester, dummy_multiple_testsuites):
    hook_recorder = pytester.inline_run(
        str(dummy_multiple_testsuites), "--collectonly", "--tags", "nonexistent=breaks"
    )

    assert len(hook_recorder.getcalls("pytest_collection")) > 0
    assert len(hook_recorder.getcalls("pytest_collection_modifyitems")) == 0
    assert len(hook_recorder.getcalls("pytest_collection_finish")) == 0
    assert len(hook_recorder.getcalls("pytest_sessionfinish")) > 0
