##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Load external auxiliaries
*************************

:module: ext_auxiliaries

ITF comes with some ready to use implementations of different
auxiliaries. But external auxiliaries can be used too and this file
demonstrates how to import such a external auxiliary.
"""

# this is only for example purpose, use the implementation in
# lib.auxiliaries anyway to avoid code duplication
from pykiso.lib.auxiliaries.dut_auxiliary import DUTAuxiliary
