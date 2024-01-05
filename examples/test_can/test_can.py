##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Can Auxiliary example
*********************

:module: test_can

:synopsis: Example test show how send and receive can messages from can

.. currentmodule:: test_can
"""
import logging
import threading
import time

import pykiso
from pykiso.auxiliaries import can_aux1, can_aux2
from pykiso.can_message import CanMessage
from pykiso.lib.auxiliaries.can_auxiliary import CanAuxiliary

can_aux1: CanAuxiliary
can_aux2: CanAuxiliary


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[can_aux1, can_aux2])
class CanAuxTest(pykiso.BasicTest):
    def test_send_and_receive_message(self):
        """
        Test send message and receive messages
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        send_t = threading.Thread(target=self.tx_thread, args=[can_aux1])

        send_t.start()
        time.sleep(0.3)
        # get last received message by message name
        recv_msg = can_aux2.get_last_message("Message_1")
        logging.info("Signal A = " + str(recv_msg.signals["signal_a"]))
        assert recv_msg.signals["signal_a"] == 4

        # get certain signal of last received message by message name
        recv_signal = can_aux2.get_last_signal("Message_1", "signal_a")
        logging.info("Received Signal = " + str(recv_signal))
        assert recv_signal == 4

        # wait certain time to receive specific message
        recv_msg = can_aux2.wait_for_message("Message_1", 1)
        logging.info(
            "New msg with wait Signal A = " + str(recv_msg.signals["signal_a"])
        )
        assert recv_msg.signals == {"signal_a": 7, "signal_b": 8}
        send_t.join()

    def test_wait_for_expected_signals(self):
        """
        Send messages, and wait one of them to match the expected signals
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        send_t = threading.Thread(target=self.tx_thread, args=[can_aux1])

        send_t.start()
        time.sleep(0.3)
        recv_msg = can_aux2.wait_to_match_message_with_signals(
            "Message_1", {"signal_a": 7}, 1
        )
        logging.info(f"Matched Message signals {recv_msg.signals}")
        assert recv_msg.signals == {"signal_a": 7, "signal_b": 8}
        send_t.join()

    def tx_thread(self, can_aux):
        messages_to_send = [
            CanMessage("Message_1", {"signal_a": 1, "signal_b": 2}, 3),
            CanMessage("Message_1", {"signal_a": 4, "signal_b": 5}, 6),
            CanMessage("Message_1", {"signal_a": 7, "signal_b": 8}, 9),
        ]
        # send multiple messages one by one from can auxiliary with certain interval
        for message_to_send in messages_to_send:
            can_aux.send_message(message_to_send.name, message_to_send.signals)
            time.sleep(0.2)
