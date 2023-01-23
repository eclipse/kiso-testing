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
from __future__ import annotations

import logging
import multiprocessing
import queue
from typing import TYPE_CHECKING, Any

from pykiso.connector import CChannel

if TYPE_CHECKING:
    from pykiso.lib.auxiliaries.mp_proxy_auxiliary import MpProxyAuxiliary
    from pykiso.types import ProxyReturn

log = logging.getLogger(__name__)


class CCMpProxy(CChannel):
    """Multiprocessing Proxy CChannel for multi auxiliary usage."""

    def __init__(self, **kwargs):
        """Initialize attributes."""
        kwargs.update(processing=True)
        super().__init__(**kwargs)
        # instantiate directly both queue_in and queue_out
        self.queue_in = multiprocessing.Queue()
        self.queue_out = multiprocessing.Queue()
        self.timeout = 1
        # used for physical channel attributes access from main auxiliary
        self._proxy = None
        self._physical_channel = None

    def _bind_channel_info(self, proxy_aux: MpProxyAuxiliary):
        """Bind a :py:class:`~pykiso.lib.auxiliaries.mp_proxy_auxiliary.MpProxyAuxiliary`
        instance that is instanciated in order to handle the connection of
        multiple auxiliaries to a single communication channel in order to
        hide the underlying proxy setup.

        :param proxy_aux: the proxy auxiliary instance that is holding the
            real communication channel.
        """
        self._proxy = proxy_aux
        self._physical_channel = proxy_aux.channel

    def __getattr__(self, name: str) -> Any:
        """Implement getattr to retrieve attributes from the real channel attached
        to the underlying :py:class:`~pykiso.lib.auxiliaries.mp_proxy_auxiliary.MpProxyAuxiliary`.

        :param name: name of the attribute to get.
        :raises AttributeError: if the attribute is not part of the real
            channel instance or if the real channel hasn't been bound to
            this proxy channel yet.
        :return: the found attribute value.
        """
        if self._physical_channel is not None:
            with self._proxy.lock:
                return getattr(self._physical_channel, name)
        raise AttributeError(
            f"{self.__class__.__name__} object has no attribute '{name}'"
        )

    def __getstate__(self):
        """Avoid getattr to be called on pickling before instanciation,
        which would cause infinite recursion.
        """
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def _cc_open(self) -> None:
        """Open proxy channel.

        Due to usage of multiprocessing the queue_in and queue_out state
        doesn't have to change in order to ensure that ProxyAuxiliary
        works even if suspend or resume is called.
        """
        log.internal_debug("Open proxy channel")

    def _cc_close(self) -> None:
        """Close proxy channel.

        Due to usage of multiprocessing the queue_in and queue_out state
        doesn't have to change in order to ensure that ProxyAuxiliary
        works even if suspend or resume is called.
        """
        log.internal_debug("Close proxy channel")

    def _cc_send(self, *args: tuple, **kwargs: dict) -> None:
        """Populate the queue in of the proxy connector.

        :param args: tuple containing positionnal arguments
        :param kwargs: dictionary containing named arguments
        """
        log.internal_debug(f"put at proxy level: {args} {kwargs}")
        self.queue_in.put((args, kwargs))

    def _cc_receive(self, timeout: float = 0.1) -> ProxyReturn:
        """Depopulate the queue out of the proxy connector.

        :param timeout: not used

        :return: bytes and source when it exist. if queue timeout
            is reached return None
        """
        try:
            return_response = self.queue_out.get(True, self.timeout)
            log.internal_debug(f"received at proxy level : {return_response}")
            return return_response
        except queue.Empty:
            return {"msg": None}
