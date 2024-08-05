##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication auxiliary usage example
*************************************

:module: test_com

:synopsis: show how to use a communication auxiliary

.. currentmodule:: test_com
"""

import logging
import time

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import com_aux
from pykiso.lib.connectors.cc_raw_loopback import CCLoopback


@pykiso.define_test_parameters(
    suite_id=3,
    case_id=4,
    aux_list=[com_aux],
)
class TestCaseOverride(pykiso.BasicTest):
    """In this test case we will simply use the two available methods
    for a communication auxiliary (send_message and receive_message)
    """

    def setUp(self):
        """If a fixture is not use just override it like below."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # due to the fact that auto_start flag is set to False, this let
        # the user to start the auxiliary on demand using start method
        com_aux.start()

        # just suspend the current auxiliary execution
        com_aux.suspend()
        # just resume the current auxiliary execution
        com_aux.resume()

    def test_run(self):
        """Thanks to the usage of dev cc_raw_loopback, let's try to send
        a message and receive it.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # send 20 requests (with the context manager over the connected channel
        #  and check if the command was successfully sent
        with com_aux.collect_messages():
            for _ in range(20):
                req = b"\x02\x04\x06"
                logging.info(f"send request {req} over {com_aux.name}")
                state = com_aux.send_message(req)
                logging.info(f"request execution state: {state}")
                self.assertEqual(state, True)
                response = com_aux.receive_message()
                logging.info(f"received data {response}")
                self.assertEqual(response, b"\x02\x04\x06")

        self.assertTrue(com_aux.queue_out.empty())

        # sending one request just to make sure queue is not empty
        with com_aux.collect_messages():
            req = b"\x02\x04\x06"
            com_aux.send_message(req)

        # check queue clearing process
        self.assertFalse(com_aux.queue_out.empty())
        com_aux.clear_buffer()
        self.assertTrue(com_aux.queue_out.empty())

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
