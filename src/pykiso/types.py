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
import sys
from types import TracebackType
from typing import Any, Dict, List, NewType, Optional, Tuple, Type, Union

if sys.version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

from . import message

PathType = Union[str, pathlib.Path]

MsgType = Union[message.Message, bytes, str]

ExcInfoType = Tuple[Type[BaseException], BaseException, TracebackType]

ProxyReturn = Union[
    Dict[str, Union[bytes, int]],
    Dict[str, Union[bytes, None]],
    Dict[str, Union[message.Message, None]],
    Dict[str, None],
]

AuxiliaryAlias = NewType("AuxiliaryAlias", str)
ConnectorAlias = NewType("ConnectorAlias", str)


class AuxiliaryConfig(TypedDict):
    connectors: Dict[str, ConnectorAlias]
    config: Dict[str, Optional[Dict[str, Any]]]
    type: str


class ConnectorConfig(TypedDict):
    config: Dict[str, Optional[Dict[str, Any]]]
    type: str


class SuiteConfig(TypedDict):
    suite_dir: str
    test_filter_pattern: str
    test_suite_id: int


class ConfigDict(TypedDict):
    auxiliaries: Dict[AuxiliaryAlias, AuxiliaryConfig]
    connectors: Dict[ConnectorAlias, ConnectorConfig]
    test_suite_list: List[SuiteConfig]
