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
import multiprocessing
import queue
from typing import Dict, Union

from pykiso import Message
from pykiso.connector import CChannel

log = logging.getLogger(__name__)

ProxyReturn = Union[
    Dict[str, Union[bytes, int]],
    Dict[str, Union[bytes, None]],
    Dict[str, Union[Message, None]],
    Dict[str, Union[None, None]],
]


class CCMpProxy(CChannel):
    """Multiprocessing Proxy CChannel for multi auxiliary usage."""

    def __init__(self, **kwargs):
        """Initialize attributes."""
        super().__init__(**kwargs)
        # instantiate directly both queue_in and queue_out
        self.queue_in = multiprocessing.Queue()
        self.queue_out = multiprocessing.Queue()
        self.timeout = 1

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

    def _cc_receive(self, timeout: float = 0.1, raw: bool = False) -> ProxyReturn:
        """Depopulate the queue out of the proxy connector.

        :param timeout: not used
        :param raw: not used

        :return: raw bytes and source when it exist. if queue timeout
            is reached return None
        """
        try:
            return_response = self.queue_out.get(True, self.timeout)
            log.internal_debug(f"received at proxy level : {return_response}")
            return return_response
        except queue.Empty:
            return {"msg": None}
