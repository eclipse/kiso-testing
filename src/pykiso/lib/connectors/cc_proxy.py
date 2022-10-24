##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Proxy Channel
*************

:module: cc_proxy

:synopsis: CChannel implementation for multi-auxiliary usage.

CCProxy channel was created, in order to enable the connection of
multiple auxiliaries on one and only one CChannel. This CChannel
has to be used with a so called proxy auxiliary.

.. currentmodule:: cc_proxy

"""
from __future__ import annotations

import logging
import queue
import threading
from typing import TYPE_CHECKING, Any, Callable

from pykiso.connector import CChannel

if TYPE_CHECKING:
    from pykiso.types import ProxyReturn


log = logging.getLogger(__name__)


class CCProxy(CChannel):
    """Proxy CChannel to bind multiple auxiliaries to a single 'physical' CChannel."""

    def __init__(self, **kwargs):
        """Initialize attributes."""
        super().__init__(**kwargs)
        self.queue_out = None
        self.timeout = 1
        self._lock = threading.Lock()
        self._tx_callback = None

    def detach_tx_callback(self) -> None:
        """Detach the current callback."""
        with self._lock:
            log.internal_warning("reset current attached transmit callback!")
            self._tx_callback = None

    def attach_tx_callback(self, func: Callable) -> None:
        """Attach to a callback to the _cc_send method.

        :param func: function to call when _cc_send is called
        """
        with self._lock:
            log.internal_debug(f"attached function {func.__name__}")
            if self._tx_callback is not None:
                log.internal_warning(
                    f"function {func.__name__} will replace current transmit callback {self._tx_callback.__name__}"
                )
            self._tx_callback = func

    def _cc_open(self) -> None:
        """Open proxy channel."""
        log.internal_info("Open proxy channel")
        self.queue_out = queue.Queue()

    def _cc_close(self) -> None:
        """Close proxy channel."""
        log.internal_debug("Close proxy channel")
        self.queue_out = queue.Queue()

    def _cc_send(self, *args: Any, **kwargs: Any) -> None:
        """Call the attached ProxyAuxiliary's transmission callback
        with the provided arguments.

        :param args: positionnal arguments to pass to the callback
        :param kwargs: named arguments to pass to the callback
        """
        log.internal_debug(f"put at proxy level: {args} {kwargs}")
        if self._tx_callback is not None:
            # call the attached ProxyAuxiliary's run_command method
            self._tx_callback(self, *args, **kwargs)

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
