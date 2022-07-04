##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
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
from pykiso.auxiliaries import record_aux

logging = logging.getLogger(__name__)


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[])
class TestWithPowerSupply(pykiso.BasicTest):
    def generate_new_log(self, msg: bytes):
        return record_aux.channel._cc_send(msg)

    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} --------------"
        )

    def test_run(self):
        """"""
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ----------------"
        )
        header = record_aux.new_log()
        self.assertEqual(header, "Received data :")

        self.generate_new_log(msg=b"log1")
        time.sleep(1)
        new_log = record_aux.new_log()
        self.assertEqual(new_log, "\nlog1")
        logging.info(new_log)

        self.generate_new_log(msg=b"log2")
        time.sleep(1)
        new_log = record_aux.new_log()
        self.assertEqual(new_log, "\nlog2")
        logging.info(new_log)

        logging.info(record_aux.get_data())

        # search regex
        logging.info(record_aux.search_regex_current_string(regex=r"log\d"))

        # clear data and check
        record_aux.clear_buffer()
        logging.info(record_aux.get_data())

        # create a file where it write recorded data. as log is empty, will not return any file
        record_aux.dump_to_file(filename="record_example.txt")

        record_aux.stop_recording()

        logging.info("Sleep 1 Seconds to do something else with the channel.")
        time.sleep(1)

        record_aux.start_recording()
        time.sleep(1)  # Time for the channel to get opened
        header = record_aux.new_log()
        self.assertEqual(header, "Received data :")

        self.generate_new_log(msg=b"log3")
        time.sleep(1)
        new_log = record_aux.new_log()
        self.assertEqual(new_log, "\nlog3")
        logging.info(new_log)

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} -----------"
        )
