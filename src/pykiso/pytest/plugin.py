from __future__ import annotations

import logging
from functools import partial
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureDef, SubRequest
from _pytest.logging import LoggingPlugin
from _pytest.main import PytestPluginManager, Session
from _pytest.unittest import TestCaseFunction

from pykiso.config_parser import parse_config
from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface
from pykiso.logging_initializer import initialize_logging
from pykiso.test_coordinator.test_suite import flatten, tc_sort_key
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.hookimpl
def pytest_auxiliary_start(aux: DTAuxiliaryInterface):
    return aux.create_instance()


@pytest.hookimpl
def pytest_auxiliary_stop(aux: DTAuxiliaryInterface):
    return aux.delete_instance()


def pytest_addhooks(pluginmanager: PytestPluginManager):
    from pykiso.pytest import hooks

    pluginmanager.add_hookspecs(hooks)


def add_auxiliary_fixture(
    session: Session, aux_alias: str, aux_instance: DTAuxiliaryInterface
):
    def auxiliary_fixture(aux: DTAuxiliaryInterface = None):
        pytest_auxiliary_start(aux)
        yield aux
        pytest_auxiliary_stop(aux)

    # register the fixture
    aux_func = partial(auxiliary_fixture, aux=aux_instance)
    aux_func.__name__ = aux_alias
    session._fixturemanager._arg2fixturedefs[aux_alias] = [
        FixtureDef(
            argname=aux_alias,
            func=aux_func,
            scope="session",
            fixturemanager=session._fixturemanager,
            baseid=None,
            params=None,
        ),
    ]


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session: Session):
    pytest_logger: LoggingPlugin = session.config.pluginmanager.get_plugin(
        "logging-plugin"
    )

    initialize_logging(
        log_path=None,
        log_level=logging.getLevelName(pytest_logger.log_cli_level),
        report_type="text",
        verbose=True,
    )
    root_logger = logging.getLogger()

    stream_handlers = [
        hdlr for hdlr in root_logger.handlers if isinstance(hdlr, logging.StreamHandler)
    ]
    file_handlers = [
        hdlr for hdlr in root_logger.handlers if isinstance(hdlr, logging.FileHandler)
    ]

    for hdlr in stream_handlers:
        root_logger.removeHandler(hdlr)
        root_logger.addHandler(pytest_logger.log_cli_handler)

    for hdlr in file_handlers:
        root_logger.removeHandler(hdlr)
        root_logger.addHandler(pytest_logger.log_file_handler)


def pytest_collection(session: Session):

    for arg in session.config.args:
        if arg.endswith(".yaml"):
            # parse the provided YAML file
            parsed_cfg = parse_config(arg)
            # register auxiliaries and associated connectors
            ConfigRegistry.register_aux_con(parsed_cfg)
            ConfigRegistry.get_auxes_alias()

            for aux_name in ConfigRegistry.get_auxes_alias():
                aux_inst = ConfigRegistry._linker._aux_cache.get_instance(aux_name)
                add_auxiliary_fixture(session, aux_name, aux_inst)

            test_suites = parsed_cfg.get("test_suite_list")
            if not test_suites:
                return

            collected_test_suites = []
            for test_suite in test_suites:
                test_modules = Path(test_suite["suite_dir"]).glob(
                    f"**/{test_suite['test_filter_pattern']}"
                )
                # sort the test items separately for each defined test suite
                collected_test_items: list[TestCaseFunction] = []
                for test_module in test_modules:
                    module_collector: pytest.Module = pytest.Module.from_parent(
                        session, path=test_module
                    )
                    collected_test_items.extend(
                        [item for item in session.genitems(module_collector)]
                    )
                    collected_kiso_tc, collected_pytest_tc = (
                        list(
                            filter(
                                lambda tc: isinstance(tc, TestCaseFunction),
                                collected_test_items,
                            )
                        ),
                        list(
                            filter(
                                lambda tc: not isinstance(tc, TestCaseFunction),
                                collected_test_items,
                            )
                        ),
                    )

                collected_test_suites.append(
                    [
                        sorted(
                            collected_kiso_tc,
                            key=lambda tc: tc_sort_key(tc.parent._obj(tc.name)),
                        )
                        + collected_pytest_tc
                    ]
                )

            collected_test_items = list(flatten(collected_test_suites))

            session.config.hook.pytest_collection_modifyitems(
                session=session, config=session.config, items=collected_test_items
            )
            session.items = collected_test_items
            session.testscollected = len(session.items)
            session.config.hook.pytest_collection_finish(session=session)
            return collected_test_items


def pytest_sessionfinish(session: Session, exitstatus):
    ConfigRegistry.delete_aux_con()
