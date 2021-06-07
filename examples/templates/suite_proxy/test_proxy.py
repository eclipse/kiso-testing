##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
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
        pass

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

        # log the first 10 received messages
        for _ in range(10):
            logging.info(f"received message: {aux2.receive_message()}")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        pass
