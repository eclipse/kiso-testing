##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Serial connector usage example
******************************

:module: test_serial

:synopsis: show how to use the cc_serial connector

.. currentmodule:: test_serial
"""

import logging
import time

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import com_aux


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[com_aux],
)
class TestSerialLoopback(pykiso.BasicTest):
    """In this test we try to receive the same message which we have send.
    RX is connected to TX on a serial dongle.
    """

    def test_run(self):
        """Executing serial loopback example, let's try to send
        a message and receive it.
        """
        TEST_MESSAGE = b"Hello Pykiso"

        logging.info(f'Try to send "{TEST_MESSAGE}" through com aux...')

        recveive_buffer = b""
        com_aux.send_message(b"Hello Pykiso")

        # Read from serial till message is complete.
        start_time = time.time()
        elapsed_time = 0
        while len(recveive_buffer) != len(b"Hello Pykiso") and elapsed_time <= 5:
            recv = com_aux.receive_message(timeout_in_s=1)
            if recv is not None:
                recveive_buffer += recv
            elapsed_time = time.time() - start_time

        logging.info(f'Received "{recveive_buffer}"')

        self.assertEqual(recveive_buffer, b"Hello Pykiso")
