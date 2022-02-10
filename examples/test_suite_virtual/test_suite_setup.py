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


@pykiso.define_test_parameters(suite_id=2, aux_list=[aux_udp], setup_timeout=2)
class ReportFailedDuringSetup(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=3, aux_list=[aux_udp], setup_timeout=2)
class ReportNotImplementedDuringSetup(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=4, aux_list=[aux_udp], setup_timeout=2)
class LostComDuringSetupAck(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=5, aux_list=[aux_udp], setup_timeout=2)
class LostComDuringSetupReport(pykiso.BasicTestSuiteSetup):
    pass
