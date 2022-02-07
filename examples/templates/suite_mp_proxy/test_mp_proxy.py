##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Multiprocessing proxy auxiliary usage example
*********************************************

:module: test_proc_proxy

:synopsis: show how to use a multiprocessing proxy auxiliary

.. currentmodule:: test_proc_proxy
"""

import logging
import time

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import aux1, aux2, proxy_aux


@pykiso.define_test_parameters(
    suite_id=2,
    case_id=4,
    aux_list=[aux1, aux2],
)
class TestCaseOverride(pykiso.BasicTest):
    """In this test case we will simply use 2 communication auxiliaries
    bounded with a proxy one. The first communication auxiliary will be
    used for sending and the other one for the reception
    """

    def setUp(self):
        """If a fixture is not use just override it like below."""
        pass

    def test_run(self):
        """Just send some raw bytes using aux1 and log first 10 received
        messages using aux2.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        logging.info("Send some random messages")
        # send random messages using aux1
        aux1.send_message(b"\x01\x02\x03")
        aux1.send_message(b"\x04\x05\x06")
        aux1.send_message(b"\x07\x08\x09")

        time.sleep(2)

        logging.info("Stop all auxiliaries and restart them")
        proxy_aux.suspend()
        aux1.suspend()
        aux2.suspend()

        time.sleep(5)

        aux1.resume()
        aux2.resume()
        proxy_aux.resume()

        logging.info("Send some random messages again")
        # send random messages using again aux1
        aux1.send_message(b"\x01\x02\x03")
        aux1.send_message(b"\x04\x05\x06")
        aux1.send_message(b"\x07\x08\x09")

        # log the first 10 received messages
        for _ in range(10):
            logging.info(f"received message: {aux2.receive_message()}")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        pass
