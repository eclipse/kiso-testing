##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Virtual DUT simulation package
******************************

:module: simulated_auxiliary

:synopsis: provide a simple interface to simulate a device under test

This auxiliary can be used as a simulated version of a device under test.

The intention is to set up a pair of CChannels like a pipe, for example a
:class:`~pykiso.lib.connectors.cc_udp_server.CCUdpServer` and a :class:`~pykiso.lib.connectors.cc_udp.CCUdp`
bound to the same address.
One side of this pipe is then connected to this virtual auxiliary,
the other one to a *real* auxiliary.

The :class:`~pykiso.lib.auxiliary.simulated_auxiliary.simulated_auxiliary.SimulatedAuxiliary` will then receive messages
from the real auxiliary just like a proper TestApp on a DUT would and answer them according to a predefined
playbook.

Each predefined playbooks are linked with real auxiliary received messages, using test case and test suite ids
(see :mod:`~pykiso.lib.auxiliaries.simulated_auxiliary.simulation`).
A so called playbook, is a basic list of different :class:`~pykiso.message.Message` instances where the content
is adapted to the current context under test (simulate a communication lost, a test case run failure...).
(see :mod:`~pykiso.lib.auxiliaries.simulated_auxiliary.scenario`).
In order to increase playbook configuration flexibility, predefined and reusable responses are located
into :mod:`~pykiso.lib.auxiliaries.simulated_auxiliary.response_templates`.

.. currentmodule:: simulated_auxiliary

.. autosummary::

   pykiso.lib.auxiliaries.simulated_auxiliary.simulated_auxiliary
   pykiso.lib.auxiliaries.simulated_auxiliary.simulation
   pykiso.lib.auxiliaries.simulated_auxiliary.scenario
   pykiso.lib.auxiliaries.simulated_auxiliary.response_templates

.. automodule:: pykiso.lib.auxiliaries.simulated_auxiliary.simulated_auxiliary
   :members:

.. automodule:: pykiso.lib.auxiliaries.simulated_auxiliary.simulation
   :members:

.. automodule:: pykiso.lib.auxiliaries.simulated_auxiliary.scenario
   :members:

.. automodule:: pykiso.lib.auxiliaries.simulated_auxiliary.response_templates
   :members:

"""

from . import simulated_auxiliary, simulation
from .simulated_auxiliary import SimulatedAuxiliary
from .simulation import Simulation
