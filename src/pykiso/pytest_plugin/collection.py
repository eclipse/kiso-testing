##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test collection
***************

:module: collection

:synopsis: allow pytest to collect test suites based on pykiso YAML
    configuration files. Make defined auxiliaries available as fixtures.

"""

from __future__ import annotations

from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from _pytest.fixtures import FixtureDef
from _pytest.unittest import TestCaseFunction

from pykiso.config_parser import parse_config
from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface
from pykiso.test_coordinator.test_execution import apply_tag_filter
from pykiso.test_coordinator.test_suite import tc_sort_key
from pykiso.test_setup.config_registry import ConfigRegistry

from .utils import *

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.fixtures import FixtureRequest
    from _pytest.main import PytestPluginManager, Session
    from _pytest.nodes import Item

    from pykiso.types import AuxiliaryAlias


@export
@pytest.hookimpl
def pytest_auxiliary_start(aux: DTAuxiliaryInterface):
    return aux.create_instance()


@export
@pytest.hookimpl
def pytest_auxiliary_stop(aux: DTAuxiliaryInterface):
    return aux.delete_instance()


@export
@pytest.hookimpl
def pytest_auxiliary_load(aux: DTAuxiliaryInterface | str):
    if isinstance(aux, str):
        aux = ConfigRegistry.get_aux_by_alias(aux)
    return aux


@export
def pytest_addhooks(pluginmanager: PytestPluginManager):
    from pykiso.pytest_plugin import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_apply_tag_filter(tests: list[TestCaseFunction], user_tags: dict[str, list[str]]):
    """Filter the test cases based on user tags provided via CLI.

    .. note::

        This originates from :py:func:`pykiso.test_coordinator.test_execution.apply_tag_filter`.
        A refactoring should be made there to maximize the common codebase.


    :param tests: list of all test functions to run-
    :param user_tags: the tags provided by the user via CLI.
    :raises NameError: if none of the tags provided by the user was found
        in any test function.
    """
    found_tags = {tag_name: False for tag_name in user_tags.keys()}
    for test_case in tests:
        test_case_tags = test_case.get_closest_marker(name="tags")

        if test_case_tags is None:
            continue

        # Skip only the test cases that have a matching tag name but no matching tag value
        for cli_tag_id, cli_tag_value in user_tags.items():
            # skip any test case that doesn't define a CLI-provided tag name
            if cli_tag_id not in test_case_tags.kwargs.keys():
                test_case.add_marker(pytest.mark.skip(reason=f"provided tag {cli_tag_id!r} not present in test tags"))
                continue
            # skip any test case that which tag value don't match the provided tag's value
            cli_tag_values = cli_tag_value if isinstance(cli_tag_value, list) else [cli_tag_value]
            found_tags[cli_tag_id] = True
            if not any(cli_val in test_case_tags.kwargs[cli_tag_id] for cli_val in cli_tag_values):
                test_case.add_marker(pytest.mark.skip(reason=f"non-matching value for tag {cli_tag_id!r}"))

    # verify that each provided tag name is defined in at least one test case
    for cli_tag_name, tag_found in found_tags.items():
        if not tag_found:
            raise NameError(
                f"Provided tag {cli_tag_name!r} is not defined in any testcase.",
                cli_tag_name,
            )


def sort_and_filter_items(
    collected_suites: list[tuple[list[TestCaseFunction], list[Item]]],
    cli_tags: dict[str, list[str]],
) -> list[Item]:
    """Filters out the test cases based on the CLI-provided tags and sort the
    collected pykiso testcases in the expected order:

    * SuiteSetup1
    * TestCase1-1
    * TestCase1-2
    * SuiteTeardown1
    * SuiteSetup2
    * ...

    :param collected_suites: list of tuples containing the collected pykiso
        test cases and pytest test cases for each loaded test module.
    :param cli_tags: dictionary mapping the CLI-provided tags names to their values.
    :raises pytest.UsageError: if a tag name was not found in any of the loaded test
        cases.
    :return: a list of all collected test cases, sorted and filtered out.
    """
    collected_test_items = []
    tag_not_found_count = defaultdict(lambda: 0)
    for kiso_testcases, pytest_testcases in collected_suites:
        if cli_tags is not None:
            # retrieve original kiso unittest cases from collected testcases
            kiso_base_testcases = [get_base_testcase(tc) for tc in kiso_testcases]
            # apply filter on them
            for apply_filters in (
                lambda: apply_tag_filter(kiso_base_testcases, cli_tags),
                lambda: pytest_apply_tag_filter(pytest_testcases, cli_tags),
            ):
                try:
                    apply_filters()
                except NameError as e:
                    # as we can't verify the tags for all test suites at once
                    # keep track of those that do not have the tag defined
                    tag_name = e.args[1]
                    tag_not_found_count[tag_name] += 1
            # re-create the originally collected testcases with their skip status
            kiso_testcases = [
                TestCaseFunction.from_parent(tc_func.parent, name=tc_func.name, callobj=kiso_tc)
                for tc_func, kiso_tc in zip(kiso_testcases, kiso_base_testcases)
            ]
        # sort the kiso testcases based on their type (SuiteSetup1 -> TestCase1 -> SuiteTearDown1)
        sorted_kiso_testcases = sorted(
            kiso_testcases,
            key=lambda tc: tc_sort_key(get_base_testcase(tc)),
        )
        # group all of the collected test items (mixed kiso and pytest test items)
        collected_test_items += sorted_kiso_testcases + pytest_testcases

    # if none of the collected test suites had the tag defined, better error out than skip everything
    # this takes into account both pykiso and pytest test suites, hence the x 2
    for tag_name, not_found_count in tag_not_found_count.items():
        if not_found_count == len(collected_suites) * 2:
            raise pytest.UsageError(f"Tag {tag_name!r} was not found in any of the collected test cases.")

    return collected_test_items


def auxiliary_fixture(request: FixtureRequest, aux: AuxiliaryAlias):
    """Dynamically added fixture for each test auxiliary.

    With the appropriate hooks, a user can customize:
    - how the auxiliaries should be loaded (by default through the
        :py:class:`~pykiso.test_setup.dynamic_loader.DynamicImportLinker`)
    - how the auxiliaries should be started (by default by calling ``create_instance``)
    - how the auxiliaries should be stopped (by default by calling ``delete_instance``)

    :param request: fixture request providing access to the defined hooks.
    :param aux: alias of the auxiliary.
    :yield: the corresponding auxiliary instance.
    """
    aux = request.config.hook.pytest_auxiliary_load(aux=aux)
    request.config.hook.pytest_auxiliary_start(aux=aux)
    yield aux
    request.config.hook.pytest_auxiliary_stop(aux=aux)


def create_auxiliary_fixture(session: Session, aux_alias: str):
    """Dynamically create fixtures for the configured auxiliaries available through
    the specified alias.

    :param session: current test session.
    :param aux_alias: configured auxiliary alias under which the fixture will
        the made available.
    """

    def auxiliary_scope(
        fixture_name: AuxiliaryAlias = aux_alias,
        config: Config = session.config,
    ) -> str:
        """Return the scope for all auxiliary fixtures.

        :param fixture_name: name of the auxiliary fixture (and its alias).
            Required by pytest's FixtureDef.
        :param config: the pytest session config.
        """
        scope = config.getini("auxiliary_scope")
        return scope

    # register the fixture
    aux_func = partial(auxiliary_fixture, aux=aux_alias)
    aux_func.__name__ = aux_alias
    if tuple(map(int, pytest.__version__.split("."))) < (8, 1, 0):
        session._fixturemanager._arg2fixturedefs[aux_alias] = [
            FixtureDef(
                fixturemanager=session._fixturemanager,
                argname=aux_alias,
                func=aux_func,
                scope=auxiliary_scope,
                baseid=None,
                params=None,
            ),
        ]
    else:
        session._fixturemanager._arg2fixturedefs[aux_alias] = [
            FixtureDef(
                config=session.config,
                argname=aux_alias,
                func=aux_func,
                scope=auxiliary_scope,
                baseid=None,
                params=None,
            ),
        ]


@export
def pytest_collection(session: Session):
    """Modify pytest collection to behave like pykiso when a YAML file is provided.

    The resulting test collection can be summed up as follows:

    - If a YAML configuration file is provided as CLI argument, parse it.
    - If the parsed configuration defines test auxiliaries, create fixtures for
      each of them named with the defined auxiliary's alias.
    - If the parsed configuration defines test suites, refer to them for test
      collection. Otherwise run pytest's test collection.

    :param request: fixture request providing access to the defined hooks.
    :param aux: alias of the auxiliary.
    :yield: the corresponding auxiliary instance.
    """
    kiso_configs = [arg for arg in session.config.args if arg.endswith(".yaml")]
    if not kiso_configs:
        return

    arg = kiso_configs.pop(0)
    session.config.args.remove(arg)

    # parse the provided YAML file
    cfg = parse_config(arg)

    # register auxiliaries and associated connectors and make fixtures out of them
    ConfigRegistry.register_aux_con(cfg)
    for aux_alias in ConfigRegistry.get_auxes_alias():
        create_auxiliary_fixture(session, aux_alias)

    test_suites = cfg.get("test_suite_list")
    if not test_suites:
        return

    collected_test_suites = []
    for test_suite in test_suites:
        # get each test module within the defined suite directory that matched the pattern
        test_modules = Path(test_suite["suite_dir"]).glob(f"**/{test_suite['test_filter_pattern']}")
        # sort the test items separately for each defined test suite
        collected_kiso_testcases, collected_pytest_testcases = list(), list()
        for test_module in test_modules:
            module_collector: pytest.Module = pytest.Module.from_parent(session, path=test_module)
            for tc in session.genitems(module_collector):
                if is_kiso_testcase(tc):
                    collected_kiso_testcases.append(tc)
                else:
                    collected_pytest_testcases.append(tc)

        collected_test_suites.append([collected_kiso_testcases, collected_pytest_testcases])

    collected_test_items = sort_and_filter_items(collected_test_suites, session.config.option.tags)
    # run modifyitems hook on the collected items (allow filtering based on -k option)
    session.config.hook.pytest_collection_modifyitems(
        session=session, config=session.config, items=collected_test_items
    )

    # set required session attributes once everything has been collected and filtered out
    session.items = collected_test_items
    session.testscollected = len(collected_test_items)
    # run finish hook and return the collected items, which will disable any subsequent pytest_collection hook execution
    session.config.hook.pytest_collection_finish(session=session)
    return collected_test_items


@export
def pytest_sessionfinish(session: Session, exitstatus: pytest.ExitCode):
    if ConfigRegistry._linker is not None:
        ConfigRegistry.delete_aux_con()
