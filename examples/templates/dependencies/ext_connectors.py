##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Load external connectors
************************

:module: ext_connectors

ITF comes with some ready to use implementations of different
connectors. But external connectors can be used too and this file
demonstrates how to import such a external connector.

"""
# this is only for example purpose, use the implementation in
# lib.connectors anyway to avoid code duplication
from pykiso.lib.connectors.cc_example import CCExample
