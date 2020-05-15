"""
Define some recurring typing definitions
"""

import typing
import pathlib
from pykiso import Message

PathType = typing.Union[str, pathlib.Path]
MsgType = typing.Union[Message, bytes, str]
