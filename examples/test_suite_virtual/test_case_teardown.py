##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import unittest

import pykiso
from pykiso import message
from pykiso.test_coordinator.test_message_handler import (
    handle_basic_interaction,
)

from pykiso.auxiliaries import aux_virtual, aux_udp  # isort:skip


@pykiso.define_test_parameters(
    suite_id=1, case_id=10, aux_list=[aux_udp], teardown_timeout=2
)
class ReportFailedDuringTearDown(pykiso.BasicTest):
    pass


@pykiso.define_test_parameters(
    suite_id=1, case_id=11, aux_list=[aux_udp], teardown_timeout=2
)
class ReportNotImplementedDuringTearDown(pykiso.BasicTest):
    pass


@pykiso.define_test_parameters(
    suite_id=1, case_id=12, aux_list=[aux_udp], teardown_timeout=2
)
class LostComDuringTearDownAck(pykiso.BasicTest):
    pass


@pykiso.define_test_parameters(
    suite_id=1, case_id=13, aux_list=[aux_udp], teardown_timeout=2
)
class LostComDuringTearDownReport(pykiso.BasicTest):
    pass
