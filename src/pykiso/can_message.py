##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
pykiso Control Message Protocol
*******************************

:module: can_message

:synopsis: Message transfer by can

.. currentmodule:: message
"""

from typing import Any


class CanMessage:
    def __init__(self, name: str, signals: dict[str, Any], timestamp: float) -> None:
        self.name = name
        self.signals = signals
        self.timestamp = timestamp
