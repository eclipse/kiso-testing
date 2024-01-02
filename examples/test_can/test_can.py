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
from pykiso.lib.auxiliaries.can_auxiliary import CanAuxiliary

can_aux1: CanAuxiliary
can_aux2: CanAuxiliary


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[can_aux1, can_aux2])
class CanAuxTest(pykiso.BasicTest):
    def setUp(self):
        pass

    def test_run(self):
        """
        Send and receive signal defined in the can dbc file
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        send_t = threading.Thread(target=self.send_message, args=[can_aux1])
        recv_t = threading.Thread(
            target=self.wait_for_receive_message, args=[can_aux2, 1]
        )

        recv_t.start()
        time.sleep(0.2)
        send_t.start()
        send_t.join()
        recv_t.join()

    def tearDown(self):
        pass

    def send_message(self, can_aux):
        can_aux.send_message(
            message="Message_1", signals={"signal_a": 1, "signal_b": 2}
        )

    def wait_for_receive_message(self, can_aux, timeout):
        recv_msg = can_aux.wait_for_message("Message_1", timeout)
        assert recv_msg.signals["signal_a"] == 1
        recv_signal = can_aux.get_last_signal("Message_1", "signal_a")
        assert recv_signal == 1
