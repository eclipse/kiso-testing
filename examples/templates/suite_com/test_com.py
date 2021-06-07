##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
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

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import com_aux


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
        pass

    def test_run(self):
        """Thanks to the usage of dev cc_raw_loopback, let's try to send
        a message and receive it.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # send a some bytes
        com_aux.send_message(b"\x01\x02\x03")
        # receive some bytes and check if it was our previous sent
        # message
        response = com_aux.receive_message()
        logging.info(f"received message: {response}")
        self.assertEqual(response, b"\x01\x02\x03")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        pass
