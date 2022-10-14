##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Define some recurring typing definitions
"""

import pathlib
from types import TracebackType
from typing import Tuple, Type, Union

from . import message

PathType = Union[str, pathlib.Path]
MsgType = Union[message.Message, bytes, str]
ExcInfoType = Tuple[Type[BaseException], BaseException, TracebackType]
