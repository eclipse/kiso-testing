##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pykiso

from pykiso.auxiliaries import aux_virtual, aux_udp  # isort:skip


@pykiso.define_test_parameters(suite_id=6, aux_list=[aux_udp])
class ReportFailedDuringTearDown(pykiso.GreyTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=7, aux_list=[aux_udp])
class ReportNotImplementedDuringTearDown(pykiso.GreyTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=8, aux_list=[aux_udp])
class LostComDuringTearDownAck(pykiso.GreyTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=9, aux_list=[aux_udp])
class LostComDuringTearDownReport(pykiso.GreyTestSuiteTeardown):
    pass
