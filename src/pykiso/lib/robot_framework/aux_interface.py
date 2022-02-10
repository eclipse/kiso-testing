##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Auxiliary interface
*******************

:module: aux_interface

:synopsis: Simply stored common methods for auxiliary's when ITF is used
    with Robot framework.

.. currentmodule:: aux_interface

"""
from robot.api import logger

from ...connector import CChannel, Flasher
from ...interfaces.thread_auxiliary import AuxiliaryInterface
from ...test_setup.config_registry import ConfigRegistry


class RobotAuxInterface:
    """Common interface for all Robot auxiliary."""

    def __init__(self, aux_type: AuxiliaryInterface):
        """Initialize attributes.

        :param aux_type: auxiliary's class
        """
        self.auxes = ConfigRegistry.get_auxes_by_type(aux_type)

    def _get_aux(self, alias: str) -> AuxiliaryInterface:
        """Return the corresponding auxiliary instance according to the
        given auxiliary's alias.

        :param alias: auxiliary's alias

        :return: auxiliary instance

        :raise: KeyError when auxiliary's alias is not part of auxes
            dictionary's keys.
        """
        if alias not in self.auxes.keys():
            logger.error(
                f"Auxiliary {alias} does not exist. Check your Yaml config",
                html=True,
            )
            raise KeyError(f"Auxiliary {alias} doesn't exist")
        return self.auxes[alias]

    def _get_aux_connectors(self, alias: str) -> CChannel:
        """Return the corresponding cchannel instance according to the
        given auxiliary's alias.

        :param alias: auxiliary's alias

        :return: associated CChannel instance
        """
        aux = self._get_aux(alias)
        return aux.channel

    def _get_aux_flasher(self, alias: str) -> Flasher:
        """Return the corresponding flasher instance according to the
        given auxiliary's alias.

        :param alias: auxiliary's alias

        :return: associated Flasher instance
        """
        aux = self._get_aux(alias)
        return aux.flash
