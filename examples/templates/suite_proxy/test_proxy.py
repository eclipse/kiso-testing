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

:synopsis: show how to use a proxy auxiliary and change it
    configuration dynamically

.. currentmodule:: test_proxy
"""

import logging
import time

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import aux1, aux2, proxy_aux
from pykiso.lib.connectors.cc_raw_loopback import CCLoopback


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
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # start auxiliary one and two because I need it
        aux1.start()
        aux2.start()
        # start the proxy auxiliary in order to open the connector
        proxy_aux.start()

    def test_run(self):
        """Just send some raw bytes using aux1 and log first 100
        received messages using aux2.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        logging.info(f">> Send and receive message using the connected pcan <<")

        logging.info(f"send 300 messages using aux1/aux2")
        # just send some requests
        self._send_messages(300)
        # log the first 100 received messages, with the aux2
        self._receive_message(100)

        logging.info(
            f">> Change proxy_aux channel dynamically and continue to send/receive <<"
        )

        logging.info(f"Stop current running auxiliaries")
        self._stop_auxes()

        # save current channel used by the proxy
        self.pcan_channel = proxy_aux.channel
        # change proxy attached channel to CCLoopback
        proxy_aux.channel = CCLoopback()

        logging.info(f"Restart all auxiliaries")
        self._start_auxes()

        logging.info(f">> Send and receive message using the connected CCLoopback <<")

        logging.info(f"send 30 messages using aux1/aux2")
        # just send some requests
        self._send_messages(10)
        # log the first 10 received messages, with the aux2
        self._receive_message(10)

        logging.info(
            f">> Switch back to the pcan channel and continue to send/receive <<"
        )

        logging.info(f"Stop current running auxiliaries")
        self._stop_auxes()

        # switch back with pcan connector
        proxy_aux.channel = self.pcan_channel

        logging.info(f"Restart all auxiliaries")
        self._start_auxes()

        logging.info(f">> Send and receive message using the connected initial pcan <<")

        logging.info(f"send 30 messages using aux1/aux2")
        # just send some requests
        self._send_messages(10)
        # log the first 10 received messages, with the aux2
        self._receive_message(10)

    def _stop_auxes(self) -> None:
        """Stop all auxiliaries currently in use."""
        # always stop the proxy auxiliary at the end
        aux1.delete_instance()
        aux2.delete_instance()
        proxy_aux.delete_instance()

    def _start_auxes(self) -> None:
        """Start all configured auxiliaries."""
        # always start the proxy auxiliary at the end
        aux1.create_instance()
        aux2.create_instance()
        proxy_aux.create_instance()

    def _send_messages(self, nb_msg: int) -> None:
        """Send n messages a defined number of times.

        :param nb_msg: number of messages pack to send
        """
        for _ in range(nb_msg):
            # send random messages using aux1
            aux1.send_message(b"\x01\x02\x03")
            aux2.send_message(b"\x04\x05\x06")
            aux1.send_message(b"\x07\x08\x09")

    def _receive_message(self, nb_msg: int) -> None:
        """Get messages from the reception queue.

        :param nb_msg: number of messages to dequeue
        """
        for _ in range(nb_msg):
            logging.info(f"received message: {aux2.receive_message()}")

    def tearDown(self):
        """If a fixture is not use just override it like below."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
