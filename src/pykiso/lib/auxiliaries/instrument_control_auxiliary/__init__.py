##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Instrument Control Auxiliary
****************************

:module: instrument_control

:synopsis: provide a simple interface to control instruments using SCPI protocol.

The functionalities provided in this package may be used directly inside ITF tests
using the corresponding auxiliary, but also using a CLI.

.. warning::
   |  This auxiliary can only be used with the cc_visa or cc_tcp_ip connector.
   |  It is not intended to be used with a proxy connector.
   |  One instrument is bound to one auxiliary even if the instrument has multiple channels.

.. currentmodule:: instrument_control

.. autosummary::

   pykiso.lib.auxiliaries.instrument_control_auxiliary.instrument_control_auxiliary
   pykiso.lib.auxiliaries.instrument_control_auxiliary.instrument_control_cli
   pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_scpi_commands
   pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_instruments

.. automodule:: pykiso.lib.auxiliaries.instrument_control_auxiliary.instrument_control_auxiliary
   :members:

.. automodule:: pykiso.lib.auxiliaries.instrument_control_auxiliary.instrument_control_cli
   :members:

.. automodule:: pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_scpi_commands
   :members:

.. automodule:: pykiso.lib.auxiliaries.instrument_control_auxiliary.lib_instruments
   :members:
"""

from . import instrument_control_auxiliary, lib_instruments, lib_scpi_commands
from .instrument_control_auxiliary import InstrumentControlAuxiliary
from .lib_instruments import REGISTERED_INSTRUMENTS, SCPI_COMMANDS_DICT
from .lib_scpi_commands import LibSCPI
