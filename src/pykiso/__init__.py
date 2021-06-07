##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
pykiso - extensible framework for (embedded) integration testing.
*****************************************************************

:module: pykiso

:synopsis: ``pykiso`` is an extensible framework for (embedded) integration testing.

.. currentmodule:: pykiso

"""

__version__ = "0.9.4"


from . import auxiliary, cli, config_parser, connector, message, types
from .auxiliary import AuxiliaryInterface
from .connector import CChannel, Flasher
from .message import Message
from .test_coordinator import test_case, test_message_handler, test_suite
from .test_coordinator.test_case import BasicTest, define_test_parameters
from .test_coordinator.test_suite import (
    BasicTestSuiteSetup,
    BasicTestSuiteTeardown,
)
