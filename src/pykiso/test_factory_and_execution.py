"""
Test Coordinator
****************

:module: test_factory_and_execution

:synopsis: Create a test environment based on the supplied configuration and executed it.

.. currentmodule:: test_factory_and_execution

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

.. warning:: Still under test

.. note::
    1. Create based on a dictionary (test config entry), a list of auxiliaries
    2. Instantiate them
    3. Glob a list of test-suite folders
    4. Generate a list of test-suites with a list of test-cases
    5. Loop per suite
    6. Gather result
"""

# Import python needed modules
import logging
import unittest

# from . import auxiliaries
from . import test_suite
from .dynamic_loader import DynamicImportLinker
from typing import Dict


def create_test_suite(test_suite_dict: Dict) -> test_suite.BasicTestSuite:
    """ create a test suite based on the config dict

    :param test_suite_dict: dict created from config with keys 'suite_dir',
        'test_filter_pattern', 'test_suite_id'
    """
    return test_suite.BasicTestSuite(
        modules_to_add_dir=test_suite_dict["suite_dir"],
        test_filter_pattern=test_suite_dict["test_filter_pattern"],
        test_suite_id=test_suite_dict["test_suite_id"],
        args=[],
        kwargs={},
    )


def run(config: Dict):
    """ create test environment base on cofig and run tests

    :param config: dict from converted YAML config file"""

    con_cfg = config["connectors"]
    aux_cfg = config["auxiliaries"]
    linker = DynamicImportLinker()
    linker.install()
    for connector, con_details in con_cfg.items():
        cfg = con_details.get("config") or dict()
        linker.provide_connector(connector, con_details["type"], **cfg)
    for auxiliary, aux_details in aux_cfg.items():
        cfg = aux_details.get("config") or dict()
        linker.provide_auxiliary(
            auxiliary,
            aux_details["type"],
            aux_cons=aux_details.get("connectors") or dict(),
            **cfg,
        )

    try:
        list_of_test_suites = []
        for test_suite_configuration in config["test_suite_list"]:
            list_of_test_suites.append(create_test_suite(test_suite_configuration))
        # Start the test-suites & publish result
        for suite in list_of_test_suites:
            unittest.TextTestRunner().run(suite)
    except Exception as e:
        logging.error(e)
    finally:
        linker.uninstall()
