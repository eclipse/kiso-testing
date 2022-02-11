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

        # send random messages using aux1
        aux1.send_message(b"\x01\x02\x03")
        aux1.send_message(b"\x04\x05\x06")
        aux1.send_message(b"\x07\x08\x09")

        # Just create a copy of aux one and two
        self.aux1_copy = aux1.create_copy()
        self.aux2_copy = aux2.create_copy()
        # create a copy of proxy_aux with the brand new aux1 and aux2
        # copy
        self.proxy_copy = proxy_aux.create_copy(
            aux_list=[self.aux1_copy, self.aux2_copy]
        )
        # all original auxiliaries have the auto_start falg to False,
        # so copy too. Just start them, always finish with the proxy
        # auxiliary
        self.aux1_copy.start()
        self.aux2_copy.start()
        self.proxy_copy.start()
        # send some random messages from aux1 and aux2 copies
        self.aux1_copy.send_message(b"\x10\x11\x12")
        self.aux1_copy.send_message(b"\x13\x14\x15")
        self.aux2_copy.send_message(b"\x16\x17\x18")
        # just wait a little bit to be sure everything is sent
        time.sleep(1)

        # destroy the all the copies
        proxy_aux.destroy_copy()
        aux2.destroy_copy()
        aux1.destroy_copy()

        # log the first 10 received messages, with the "original" aux2
        for _ in range(10):
            logging.info(f"received message: {aux2.receive_message()}")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        pass
