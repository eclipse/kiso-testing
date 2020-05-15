"""
pykiso - extensible framework for (embedded) integration testing.
*****************************************************************

:module: pykiso

:synopsis: ``pykiso`` is an extensible framework for (embedded) integration testing.

.. currentmodule:: pykiso

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.
"""

__version__ = "0.1.0"


from . import message
from .message import Message

from . import connector
from .connector import CChannel
from .connector import Flasher

from . import auxiliary
from .auxiliary import AuxiliaryInterface

from . import test_case
from .test_case import define_test_parameters
from .test_case import BasicTest

from . import test_suite
from .test_suite import BasicTestSuiteTeardown
from .test_suite import BasicTestSuiteSetup

from . import types
from . import cli
