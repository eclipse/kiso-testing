##########################################################################
# Copyright (c) 2023-2023 Accenture
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
test_suite_1
************
:module: test_suite_1
:synopsis: Showcase of grpc with pykiso
"""

import importlib
import logging

import pykiso
from pykiso.auxiliaries import com_aux


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[com_aux])
class DefaultTest(pykiso.BasicTest):
    """With default parameters"""

    def test_run(self):
        answer = com_aux.send_message("")
        assert answer == "Hello World!"


@pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=[com_aux])
class SpecificTest(pykiso.BasicTest):
    """With specific parameters"""

    def test_run(self):
        answer = com_aux.send_message(
            "",
            service_name="Greeter",
            rpc_name="SayHello",
            message_name="HelloRequest",
            message_fields={"name": "World"},
        )
        assert answer == "Hello World!"
