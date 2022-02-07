##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
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
        # just create a communication auxiliary with a bran new channel
        # in order to send odd bytes. Always use named arguments!
        com_aux.start()
        self.com_aux_odd = com_aux.create_copy(com=CCLoopback())
        # just create a communication auxiliary based on the given
        # parameters present in the yaml config (com_aux.yaml) to send
        # even bytes
        self.com_aux_even = self.com_aux_odd.create_copy()
        # start com_aux_even because original configuration has
        # auto_start flag set to False
        self.com_aux_even.start()

    def test_run(self):
        """Thanks to the usage of dev cc_raw_loopback, let's try to send
        a message and receive it.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # first send the even bytes and stop the copy in order to
        # automatically resume the original one (self.com_aux_odd)
        self.com_aux_even.send_message(b"\x02\x04\x06")
        response = self.com_aux_even.receive_message()
        self.assertEqual(response, b"\x02\x04\x06")
        # destroy com_aux_even and start working with com_aux_odd aux
        # copy
        self.com_aux_odd.destroy_copy()

        # Then send the odd bytes and stop the copy in order to
        # automatically resume the original one (com_aux)
        self.com_aux_odd.send_message(b"\x01\x03\x05")
        response = self.com_aux_odd.receive_message()
        self.assertEqual(response, b"\x01\x03\x05")
        # destroy com_aux_odd and start working with com_aux
        com_aux.destroy_copy()

        # Just use the original communication auxiliary to send and
        # receive some bytes
        com_aux.send_message(b"\x01\x02\x03\x04\x05\x06")
        response = com_aux.receive_message()
        logging.info(f"received message: {response}")
        self.assertEqual(response, b"\x01\x02\x03\x04\x05\x06")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
