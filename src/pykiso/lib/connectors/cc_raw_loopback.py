"""
Loopback CChannel
*********************

:module: cc_raw_loopback

:synopsis: Loopback CChannel for testing purposes.

.. currentmodule:: cc_raw_loopback

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0
"""

import logging

from pykiso import CChannel
from pykiso.types import MsgType
from collections import deque


class CCLoopback(CChannel):
    """ Loopback CChannel for testing purposes.

    Whatever gets sent via cc_send will land in a FIFO and can be received
    via cc_receive.
    """

    def __init__(self, **kwargs):
        super(CCLoopback, self).__init__(**kwargs)
        self._loopback_buffer = None

    def _cc_open(self):
        self._loopback_buffer = deque()

    def _cc_close(self):
        self._loopback_buffer = None

    def _cc_send(self, msg: MsgType, raw: bool = True):
        self._loopback_buffer.append(msg)

    def _cc_receive(self, timeout: float, raw: bool = True) -> MsgType:
        return self._loopback_buffer.popleft()
