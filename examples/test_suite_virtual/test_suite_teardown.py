##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
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


@pykiso.define_test_parameters(suite_id=6, aux_list=[aux_udp], teardown_timeout=2)
class ReportFailedDuringTearDown(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=7, aux_list=[aux_udp], teardown_timeout=2)
class ReportNotImplementedDuringTearDown(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=8, aux_list=[aux_udp], teardown_timeout=2)
class LostComDuringTearDownAck(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=9, aux_list=[aux_udp], teardown_timeout=2)
class LostComDuringTearDownReport(pykiso.BasicTestSuiteTeardown):
    pass
