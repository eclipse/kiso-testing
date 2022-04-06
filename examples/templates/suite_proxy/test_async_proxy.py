##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Proxy auxiliary usage example
*****************************

:module: test_proxy

:synopsis: show how to use a proxy auxiliary

.. currentmodule:: test_proxy
"""

import logging
import time

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import aux1, aux2, proxy_aux


@pykiso.define_test_parameters(
    suite_id=2,
    case_id=3,
    aux_list=[aux1, aux2],
)
class TestCaseOverride(pykiso.BasicTest):
    """In this test case we will simply use 2 communication auxiliaries
    bounded with a proxy one. The first communication auxiliary will be
    used for sending and the other one for the reception
    """

    def setUp(self):
        """If a fixture is not use just override it like below."""
        # start auxiliary one and two because I need it
        aux1.start()
        aux2.start()
        # start the proxy auxiliary in order to open the connector
        proxy_aux.start()

    def test_run(self):
        """Just send some raw bytes using aux1 and log first 10 received
        messages using aux2.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # Simple send and receive
        question = b"\x01\x02\x03"
        aux1.send_message(question)
        time.sleep(10)
        # Reception from proxy
        answer = aux2.receive_message(True, 5)
        self.assertEqual(question, answer)
        # Reception from loopback
        answer = aux2.receive_message(True, 5)
        self.assertEqual(question, answer)

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        pass
