##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test-App : Override default test implementation
***********************************************

:module: test_override

:synopsis: show how customize your test fixtures by re-implemnenting
    them partially or completely. In addition, we will see some
    DutAuxiliary's features like suspend, resume....

.. currentmodule:: test_override
"""

import logging

import pykiso
from pykiso import message
from pykiso.auxiliaries import aux1, aux2


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=2,
    aux_list=[aux1],
)
class TestCaseOverride(pykiso.BasicTest):
    """In this test case we will simply re-implement test_run, setUp,
    tearDown methods to re-define the default Test-App behavior of ITF
    BasicTest.
    """

    def setUp(self):
        """Let's say, we want to suspend aux2, execute default
        implemented setup test (for aux1) and resume the paused aux2.
        """
        # call BasicTest base class setup method
        super().setUp()
        # make some extra logging and suspend aux2
        logging.info("------------suspend aux2 run-------------")
        aux2.suspend()
        # make some extra logging and resume aux2
        logging.info("------------resume aux2 run--------------")
        aux2.resume()

    def test_run(self):
        """Let's say now, we want to send a command message with our
        aux1 and check if we get a ack message and make some extra
        logging for the received report.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        awesome_message = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=message.MessageCommandType.TEST_CASE_RUN,
            test_suite=self.test_suite_id,
            test_case=self.test_case_id,
        )

        state = aux1.run_command(awesome_message, blocking=True, timeout_in_s=10)

        self.assertEqual(state, True)

        report = aux1.wait_and_get_report(blocking=True, timeout_in_s=5)

        logging.info(f"Received report message from DUT : {report}")

    def tearDown(self):
        """Finally I just want to show a warning message telling that
        no tearDown is implemented for test suite 1 and test case 2 on
        DUT side."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        logging.warning("No test case teardown implemented for TS:1 TC:2")
