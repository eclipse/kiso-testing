##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Config Registry
***************

:module: config_registry

:synopsis: register auxiliaries and connectors to provide them for import.

.. currentmodule:: config_registry

"""

from typing import Any

from .dynamic_loader import DynamicImportLinker


class ConfigRegistry:
    """Register auxiliaries with connectors to provide systemwide import statements."""

    _linker = None

    @classmethod
    def register_aux_con(cls, config: dict) -> None:
        """Create import hooks. Register auxiliaries and connectors.

        :param config: dictionary containing yaml configuration content
        """
        ConfigRegistry._linker = DynamicImportLinker()
        ConfigRegistry._linker.install()
        for connector, con_details in config["connectors"].items():
            cfg = con_details.get("config") or dict()
            ConfigRegistry._linker.provide_connector(
                connector, con_details["type"], **cfg
            )
        for auxiliary, aux_details in config["auxiliaries"].items():
            cfg = aux_details.get("config") or dict()
            ConfigRegistry._linker.provide_auxiliary(
                auxiliary,
                aux_details["type"],
                aux_cons=aux_details.get("connectors") or dict(),
                **cfg,
            )

    @classmethod
    def delete_aux_con(cls) -> None:
        """deregister the import hooks, close all running threads, delete all instances."""
        ConfigRegistry._linker.uninstall()

    @classmethod
    def get_all_auxes(cls) -> dict:
        """Return all auxiliaires instances and alias

        :return: dictionary with alias as keys and instances as values
        """
        return ConfigRegistry._linker._aux_cache.instances

    @classmethod
    def get_auxes_by_type(cls, aux_type: Any) -> dict:
        """Return all auxiliaries who match a specific type.

        :param aux_type: auxiliary class type (DUTAuxiliary,
            CommunicationAuxiliary...)

        :return: dictionary with alias as keys and instances as values
        """
        all_auxes = ConfigRegistry._linker._aux_cache.instances
        return {
            alias: inst
            for alias, inst in all_auxes.items()
            if isinstance(inst, aux_type)
        }

    @classmethod
    def get_aux_by_alias(cls, alias: str) -> Any:
        """Return the associated auxiliary instance to the given alias.

        :param alias: auxiliary's alias

        :return: auxiliary instance created by the dymanic loader
        """
        return ConfigRegistry._linker._aux_cache.get_instance(alias)

    @classmethod
    def get_aux_config(cls, name: str) -> dict:
        """Return the registered auxiliary configuration based on his
        name.

        :param name: auxiliary alias

        :return: auxiliary's configuration (yaml content)
        """
        return ConfigRegistry._linker._aux_cache.configs[name]

    @classmethod
    def get_auxes_alias(cls) -> list:
        """return all created auxiliaries alias.

        :return: list containing all auxiliaries alias
        """
        return [alias for alias in ConfigRegistry._linker._aux_cache.connectors.keys()]
