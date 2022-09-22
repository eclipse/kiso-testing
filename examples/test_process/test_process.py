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
import sys
import time
from pathlib import Path

import pykiso

executable = str(Path(sys.executable).resolve())

# as usual import your auxiliairies
from pykiso.auxiliaries import com_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[com_aux])
class TestProcess(pykiso.BasicTest):
    """In this test we try to receive the same message which we have send.
    RX is connected to TX on a serial dongle.
    """

    def test_run(self):
        com_aux.send_message(
            {
                "command": "start",
                "executable": executable,
                "args": [
                    "-c",
                    'import sys;import time;time.sleep(1);print(\'error\', file=sys.stderr);sys.stderr.flush();print("hello");sys.stdout.flush();time.sleep(1);print("pykiso2")',
                ],
            }
        )

        while True:
            recv = com_aux.receive_message()
            logging.info(f'Received "{recv}"')
            if "exit" in recv:
                break
