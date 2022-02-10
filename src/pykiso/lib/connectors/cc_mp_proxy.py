##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Multiprocessing Proxy Channel
*****************************

:module: cc_mp_proxy

:synopsis: concrete implementation of a multiprocessing proxy channel

CCProxy channel was created, in order to enable the connection of
multiple auxiliaries on one and only one CChannel. This CChannel
has to be used with a so called proxy auxiliary.

.. currentmodule:: cc_mp_proxy

"""

import logging
from multiprocessing import Queue

from pykiso.lib.connectors.cc_proxy import CCProxy

log = logging.getLogger(__name__)


class CCMpProxy(CCProxy):
    """Multiprocessing Proxy CChannel for multi auxiliary usage."""

    def __init__(self, **kwargs):
        """Initialize attributes."""

        super().__init__(**kwargs)
        # instantiate directly both queue_in and queue_out
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.timeout = 1

    def _cc_open(self) -> None:
        """Open proxy channel.

        Due to usage of multiprocessing the queue_in and queue_out state
        doesn't have to change in order to ensure that ProxyAuxiliary
        works even if suspend or resume is called.
        """
        log.debug("Open proxy channel")

    def _cc_close(self) -> None:
        """Close proxy channel.

        Due to usage of multiprocessing the queue_in and queue_out state
        doesn't have to change in order to ensure that ProxyAuxiliary
        works even if suspend or resume is called.
        """
        log.debug("Close proxy channel")
