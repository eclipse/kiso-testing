##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
#
# This source code is copyright protected and proprietary
# to Robert Bosch GmbH. Only those rights that have been
# explicitly granted to you by Robert Bosch GmbH in written
# form may be exercised. All other rights remain with
# Robert Bosch GmbH.
##########################################################################

"""
DBC parser
*****************************

:module: parser

:synopsis: A parser class that wraps the passed eBike DBC to
    encode and decode messages.

.. currentmodule:: parser
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cantools.database import Database, Message


if TYPE_CHECKING:
    from .config import IdentificationData1, IdentificationData2

log = logging.getLogger(__name__)


class CanMessageParser:
    """A message parser and builder"""
    def __init__(self, dbc_path: Path) -> None:
        """Initialize all eShift-specific messages as attributes using
        the provided eBike DBC.

        :param dbc_path: path to the eBike CAN database containing the
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

        .. note:: For the sake of simplicity, the decoding of choices as litterals
            is disabled.

        :param data: encoded message data.
        :param frame_id: frame ID the encoded message was received on.
        :return: the decoded message as a dictionary.
        """
        return self.dbc.decode_message(frame_id, data, decode_choices=False)
