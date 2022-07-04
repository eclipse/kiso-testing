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


@pykiso.define_test_parameters(suite_id=1, case_id=10, aux_list=[aux_udp])
class ReportFailedDuringTearDown(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=11, aux_list=[aux_udp])
class ReportNotImplementedDuringTearDown(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=12, aux_list=[aux_udp])
class LostComDuringTearDownAck(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=13, aux_list=[aux_udp])
class LostComDuringTearDownReport(pykiso.RemoteTest):
    pass
