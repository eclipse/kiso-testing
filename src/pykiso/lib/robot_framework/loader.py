##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Dynamic Loader plugin
*********************

:module: loader

:synopsis: implementation of existing magic import mechanism from ITF
    for Robot framework usage.

.. currentmodule:: loader

"""

import importlib
import sys
from pathlib import Path
from typing import List

from robot.api import logger
from robot.api.deco import keyword, library

from ...cli import parse_config
from ...test_setup.config_registry import ConfigRegistry
from ...test_setup.dynamic_loader import PACKAGE
from ..auxiliaries.proxy_auxiliary import ProxyAuxiliary


@library(version="0.1.0")
class RobotLoader:
    """Robot framework plugin for ITF magic import mechanism."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, config_file: Path):
        """Initialize attributes.

        :param config_file : yaml configuration file path
        """
        self.config_file = parse_config(config_file)
        self.auxiliaries = {}

    def _detect_proxy_auxes(self) -> List[str]:
        """Detect all proxy auxiliaires from yaml configuration file.

        :return: list containing all proxy auxiliairies alias
        """
        proxy_aux_alias = []
        for alias, aux_conf in self.config_file["auxiliaries"].items():
            if ProxyAuxiliary.__name__ in aux_conf["type"]:
                proxy_aux_alias.append(alias)
        return proxy_aux_alias

    @keyword(name="install")
    def install(self) -> None:
        """Provide, create and import auxiliaires/connectors present
        within yaml configuration file.

        :raises: re-raise the caught exception (Exception level)
        """
        try:
            ConfigRegistry.register_aux_con(self.config_file)
            proxy_auxes = self._detect_proxy_auxes()
            auxes_alias = ConfigRegistry.get_auxes_alias()

            # import all auxiliaries except proxy ones
            for alias in auxes_alias:
                if alias not in proxy_auxes:
                    self.auxiliaries[alias] = importlib.import_module(
                        f".{alias}", f"{PACKAGE}.auxiliaries"
                    )
            # finally install proxy auxiliaries
            for alias in proxy_auxes:
                self.auxiliaries[alias] = importlib.import_module(
                    f".{alias}", f"{PACKAGE}.auxiliaries"
                )
            logger.info(f"auxiliaries {self.auxiliaries} installed")
        except Exception as error:
            logger.error(
                f"An error occurred during auxiliaries creation, reason : {error}"
            )
            raise

    @keyword(name="uninstall")
    def uninstall(self) -> None:
        """Uninstall all created instances of auxiliaires/connectors.

        :raises: re-raise the caught exception (Exception level)
        """
        try:
            ConfigRegistry.delete_aux_con()
            for alias in self.auxiliaries:
                sys.modules.pop(f"{PACKAGE}.auxiliaries.{alias}")
            logger.info(f"auxiliaries {self.auxiliaries} uninstalled")
        except Exception as error:
            logger.error(
                f"An error occurred during auxiliaries deletion, reason : {error}"
            )
            raise
