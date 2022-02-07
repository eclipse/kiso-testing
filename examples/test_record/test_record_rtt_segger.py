##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Record auxiliary test
*********************

:module: test_record

:synopsis: Example test that shows how to record a connector

.. currentmodule:: test_record

"""

import logging
import time

import pykiso

# !!! IMPORTANT !!!
# To start recording the channel which are specified in the yaml file,
# the record_aux must be first imported here.
# The channel recording will then run automatically in the background.
from pykiso.auxiliaries import record_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[])
class TestWithPowerSupply(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} --------------"
        )

    def test_run(self):
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ----------------"
        )

        logging.info(
            "Sleep 5 Seconds. Record specified channel from .yaml in the background."
        )
        time.sleep(5)

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} -----------"
        )
