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


@pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=[aux_udp])
class ReportFailedDuringSetup(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=3, aux_list=[aux_udp])
class ReportNotImplementedDuringSetup(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=4, aux_list=[aux_udp])
class LostComDuringSetupAck(pykiso.RemoteTest):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=5, aux_list=[aux_udp])
class LostComDuringSetupReport(pykiso.RemoteTest):
    pass
