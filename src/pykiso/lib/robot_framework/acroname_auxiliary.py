##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
acroname auxiliary plugin
*************************

:module: acroname_auxiliary

:synopsis: implementation of existing AcronameAuxiliary for
    Robot framework usage.

.. currentmodule:: acroname_auxiliary

"""

from typing import Optional

from robot.api.deco import keyword, library

from ..auxiliaries.acroname_auxiliary import AcronameAuxiliary as AcroAux
from .aux_interface import RobotAuxInterface


@library(version="0.1.0")
class AcronameAuxiliary(RobotAuxInterface):
    """Robot framework plugin for AcronameAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=AcroAux)

    @keyword(name="Set port enable")
    def set_port_enable(self, aux_alias: str, port: int) -> int:
        """Enable power and data lines for a USB port.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :return: brainstem error code. 0 if no error.
        """
        aux = self._get_aux(aux_alias)
        return aux.set_port_enable(port)

    @keyword(name="Set port disable")
    def set_port_disable(self, aux_alias: str, port: int) -> int:
        """Disable power and data lines for a USB port.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :return: brainstem error code. 0 if no error.
        """
        aux = self._get_aux(aux_alias)
        return aux.set_port_disable(port)

    @keyword(name="Get port current")
    def get_port_current(
        self, aux_alias: str, port: int, unit: str = "A"
    ) -> Optional[float]:
        """Get the current through the power line for selected usb port.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :param unit: unit of the result in "uA", "mA" or "A". Default "A"
        :return: port current for given unit. None if unit is not supported.
        """
        aux = self._get_aux(aux_alias)
        return aux.get_port_current(port, unit)

    @keyword(name="Get port voltage")
    def get_port_voltage(
        self, aux_alias: str, port: int, unit: str = "V"
    ) -> Optional[float]:
        """Get the voltage of the selected usb port.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :param unit: unit of the result in "uV", "mV" or "V". Default "V"
        :return: port voltage for given unit. None if unit is not supported.
        """
        aux = self._get_aux(aux_alias)
        return aux.get_port_voltage(port, unit)

    @keyword(name="Get port current limit")
    def get_port_current_limit(
        self, aux_alias: str, port: int, unit: str = "A"
    ) -> Optional[float]:
        """Get the current limit for the port.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :param unit: unit of the result in "uA", "mA" or "A". Default "A"
        :return: port current limit for given unit. None if unit is not supported.
        """
        aux = self._get_aux(aux_alias)
        return aux.get_port_current_limit(port, unit)

    @keyword(name="Set port current limit")
    def set_port_current_limit(
        self, aux_alias: str, port: int, amps: float, unit: str = "A"
    ) -> None:
        """Set the current limit for the port. If the set limit is not achievable,
        devices will round down to the nearest available current limit setting.

        :param aux_alias: auxiliary's alias
        :param port: the USB port number
        :param amps: value for port current to set in "uA", "mA" or "A". Default "A"
        :param unit: unit for the value to set. Default Ampere
        """
        aux = self._get_aux(aux_alias)
        return aux.set_port_current_limit(port, amps, unit)
