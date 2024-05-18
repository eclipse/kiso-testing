##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
DBC parser
**********

:module: parser

:synopsis: A parser class that wraps the passed DBC to
    encode and decode messages.

.. currentmodule:: parser
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from cantools.database import Database, Message

log = logging.getLogger(__name__)


class CanMessageParser:
    """A message parser and builder"""

    def __init__(self, dbc_path: Path) -> None:
        """Can dbc file parser

        :param dbc_path: path to the CAN database containing the
            message information.
        """

        self.dbc = Database()
        self.dbc.add_dbc_file(dbc_path)

    def encode(self, msg: Message, msg_data: dict[str, Any]) -> tuple[bytes, int]:
        """Encode a message according to the DBC.

        :param msg: message instance.
        :param msg_data: message data.
        :return: a tuple containing the encoded message data and the frame ID
            it should be sent on.
        """
        log.debug("Encoding message to send %s", msg_data)
        return msg.encode(msg_data), msg.frame_id

    def decode(self, data: bytes, frame_id: int) -> dict[str, int]:
        """Decode a message according to the DBC.

        .. note:: For the sake of simplicity, the decoding of choices as literals
            is disabled.

        :param data: encoded message data.
        :param frame_id: frame ID the encoded message was received on.
        :return: the decoded message as a dictionary.
        """
        return self.dbc.decode_message(frame_id, data, decode_choices=False)
