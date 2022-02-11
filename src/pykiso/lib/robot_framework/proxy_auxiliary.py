##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Proxy auxiliary plugin
**********************

:module: proxy_auxiliary

:synopsis: implementation of existing ProxyAuxiliary for Robot
    framework usage.

.. currentmodule:: proxy_auxiliary

"""

from robot.api.deco import keyword, library

from ..auxiliaries.mp_proxy_auxiliary import MpProxyAuxiliary as MpProxyAux
from ..auxiliaries.proxy_auxiliary import ProxyAuxiliary as ProxyAux
from .aux_interface import RobotAuxInterface


@library(version="0.1.0")
class ProxyAuxiliary(RobotAuxInterface):
    """Robot framework plugin for ProxyAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=ProxyAux)

    @keyword(name="Suspend")
    def suspend(self, aux_alias: str) -> None:
        """Suspend given auxiliary's run.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.suspend()

    @keyword(name="Resume")
    def resume(self, aux_alias: str) -> None:
        """Resume given auxiliary's run.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.resume()


@library(version="0.1.0")
class MpProxyAuxiliary(RobotAuxInterface):
    """Robot framework plugin for MpProxyAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=MpProxyAux)

    @keyword(name="Suspend")
    def suspend(self, aux_alias: str) -> None:
        """Suspend given auxiliary's run.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.suspend()

    @keyword(name="Resume")
    def resume(self, aux_alias: str) -> None:
        """Resume given auxiliary's run.

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.resume()
