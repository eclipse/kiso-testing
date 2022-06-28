##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Configuration access example
****************************

:module: test_access

:synopsis: just a basic example on how to access configuration
    information fron test case level
"""

import logging

import pykiso
from pykiso.auxiliaries import aux1, aux2, aux3
from pykiso.global_config import GlobalConfig

# get all parameters given at yaml configuration level
yaml_config = GlobalConfig().yaml
# store all auxiliaries configuration
aux_config = yaml_config.auxiliaries
# store all connectors configuration
con_config = yaml_config.connectors
# get all parameters given at cli level
cli_config = GlobalConfig().cli


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[aux1, aux2],
    setup_timeout=1,
    teardown_timeout=1,
    tag={"variant": ["variant2", "variant1"], "branch_level": ["daily", "nightly"]},
)
class MyTest1(pykiso.BasicTest):
    """Simply Test case use to show configuraton parameters access."""

    def setUp(self):
        """Just print all given cli parameters."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        logging.info("*** print all parameters given at cli level ***")
        logging.info(f"loaded configuration file: {cli_config.test_configuration_file}")
        logging.info(f"logging text file path: {cli_config.log_path}")
        logging.info(f"log level: {cli_config.log_level}")
        logging.info(f"report type: {cli_config.report_type}")
        logging.info(f"variant filter: {cli_config.variant}")
        logging.info(f"branch level: {cli_config.branch_level}")
        logging.info(f"pattern: {cli_config.pattern}")

    def test_run(self):
        """Just verify some configuration values."""
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        if yaml_config.auxiliaries.aux2.connectors.flash == "chan3":
            logging.info("Auxiliary aux2 has a flasher")

        # just make a simple assertion in order to raise an error and
        # stop test execution if a specific value is not given to chan1
        # connector
        self.assertEqual(yaml_config.connectors.chan1.config.param_1, "value 1")

    def tearDown(self):
        """Just print aux2 configuration and it related connector too."""
        logging.info(
            f"---------------TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        logging.info("*** print aux2 configuration ***")
        logging.info(f"auxiliary aux2 flasher: {aux_config.aux2.connectors.flash}")
        logging.info(f"auxiliary aux2 connector: {aux_config.aux2.connectors.com}")

        logging.info("*** print associated connector configuration ***")
        logging.info(
            f"channel chan1 param 1: {yaml_config.connectors.chan1.config.param_1}"
        )
        logging.info(
            f"channel chan1 param 2: {yaml_config.connectors.chan1.config.param_2}"
        )
        logging.info(f"channel chan1 type: {yaml_config.connectors.chan1.type}")
        logging.info(f"connector chan2 type: {yaml_config.connectors.chan2.type}")
