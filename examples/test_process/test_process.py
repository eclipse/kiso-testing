##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
process connector usage example
******************************

:module: test_process

:synopsis: show how to use the cc_process connector

.. currentmodule:: test_process
"""

import logging
import sys
import time
from pathlib import Path

import pykiso

# as usual import your auxiliairies
from pykiso.auxiliaries import com_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[com_aux])
class TestProcess(pykiso.BasicTest):
    """In this test we communicate with a python process."""

    def test_run(self):
        # Get the path of the python executable to start a python process
        executable = str(Path(sys.executable).resolve())

        # start the process
        com_aux.send_message(
            {
                "command": "start",
                "executable": executable,
                "args": [
                    "-c",
                    # process:
                    # read line from stdin and write to stdout
                    # sleep 1s
                    # print "error" on stderr
                    # sleep 1s
                    # print "hello" on stdout
                    # print "pykiso" on stdout
                    'import sys;import time;print(sys.stdin.readline().strip());sys.stdout.flush();time.sleep(1);print(\'error\', file=sys.stderr);sys.stderr.flush();time.sleep(1);print("hello");print("pykiso")',
                ],
            }
        )

        # send "hi" to stdin of the process
        com_aux.send_message("hi\n")
        recv = com_aux.receive_message()
        logging.info(f'Received "{recv}"')
        assert recv == {"stdout": "hi\n"}

        # check output of process(stdout and stderr)
        recv = com_aux.receive_message()
        logging.info(f'Received "{recv}"')
        assert recv == {"stderr": "error\n"}

        recv = com_aux.receive_message()
        logging.info(f'Received "{recv}"')
        assert recv == {"stdout": "hello\n"}

        recv = com_aux.receive_message()
        logging.info(f'Received "{recv}"')
        assert recv == {"stdout": "pykiso\n"}

        recv = com_aux.receive_message()
        logging.info(f'Received "{recv}"')
        assert recv["exit"] == 0
