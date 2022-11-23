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

from collections import defaultdict
from typing import Any, List

from pykiso.lib.auxiliaries.mp_proxy_auxiliary import MpProxyAuxiliary
from pykiso.lib.auxiliaries.proxy_auxiliary import ProxyAuxiliary
from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy
from pykiso.lib.connectors.cc_proxy import CCProxy

from .dynamic_loader import DynamicImportLinker


class ConfigRegistry:
    """Register auxiliaries with connectors to provide systemwide import
    statements.
    """

    _linker = None

    @staticmethod
    def _make_proxy_channel_config(aux_name: str, multiprocessing: bool):
        con_class = CCProxy if not multiprocessing else CCMpProxy
        name = f"proxy_channel_{aux_name}"
        config = {
            "config": None,
            "type": f"{con_class.__module__}:{con_class.__name__}",
        }
        return name, config

    @staticmethod
    def _make_proxy_aux_config(
        con_name: str, aux_list: List[str], multiprocessing: bool
    ):
        aux_class = ProxyAuxiliary if not multiprocessing else MpProxyAuxiliary
        name = f"proxy_aux_{con_name}"
        config = {
            "connectors": {"channel": con_name},
            "config": {"aux_list": aux_list},
            "type": f"{aux_class.__module__}:{aux_class.__name__}",
        }
        return name, config

    @classmethod
    def register_aux_con(cls, config: dict) -> None:
        """Create import hooks. Register auxiliaries and connectors.

        :param config: dictionary containing yaml configuration content
        """
        # Possibility 1: Pre-parse aux configurations and replace them directly with a Proxy setup config
        # 1. Detect required proxy setups
        cchannel_to_auxiliaries = defaultdict(list)
        for auxiliary, aux_details in config["auxiliaries"].items():
            try:
                cchannel = aux_details["config"]["connectors"]["com"]
            except KeyError:
                continue
            cchannel_to_auxiliaries[cchannel].append(auxiliary)

        # 2. Overwrite auxiliary and connector config with required proxies
        for channel_name, auxiliaries in cchannel_to_auxiliaries.items():
            if len(auxiliaries) < 2:
                continue
            mp_enabled = config["connectors"][channel_name]["config"].get(
                "processing", False
            )
            proxy_aux_name, proxy_aux_cfg = ConfigRegistry._make_proxy_aux_config(
                channel_name, auxiliaries, mp_enabled
            )
            config["auxiliaries"][proxy_aux_name] = proxy_aux_cfg
            for aux_name in auxiliaries:
                cc_proxy_name, cc_proxy_cfg = ConfigRegistry._make_proxy_channel_config(
                    aux_name, mp_enabled
                )
                config["connectors"][cc_proxy_name] = cc_proxy_cfg

        cls._linker = DynamicImportLinker()
        cls._linker.install()
        for connector, con_details in config["connectors"].items():
            cfg = con_details.get("config") or dict()
            cls._linker.provide_connector(connector, con_details["type"], **cfg)

        # 3. Provide auxiliaries and connectors from patched configuration
        for auxiliary, aux_details in config["auxiliaries"].items():
            cfg = aux_details.get("config") or dict()
            cls._linker.provide_auxiliary(
                auxiliary,
                aux_details["type"],
                aux_cons=aux_details.get("connectors") or dict(),
                **cfg,
            )

        # Possibility 2: Pre-parse aux configurations and provide requires_proxy to the linker

    @classmethod
    def delete_aux_con(cls) -> None:
        """Deregister the import hooks, close all running threads,
        delete all instances.
        """
        cls._linker.uninstall()

    @classmethod
    def get_all_auxes(cls) -> dict:
        """Return all auxiliaires instances and alias

        :return: dictionary with alias as keys and instances as values
        """
        return cls._linker._aux_cache.instances

    @classmethod
    def get_auxes_by_type(cls, aux_type: Any) -> dict:
        """Return all auxiliaries who match a specific type.

        :param aux_type: auxiliary class type (DUTAuxiliary,
            CommunicationAuxiliary...)

        :return: dictionary with alias as keys and instances as values
        """
        all_auxes = cls._linker._aux_cache.instances
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
        return cls._linker._aux_cache.get_instance(alias)

    @classmethod
    def get_aux_config(cls, name: str) -> dict:
        """Return the registered auxiliary configuration based on his
        name.

        :param name: auxiliary alias

        :return: auxiliary's configuration (yaml content)
        """
        return cls._linker._aux_cache.configs[name]

    @classmethod
    def get_auxes_alias(cls) -> list:
        """return all created auxiliaries alias.

        :return: list containing all auxiliaries alias
        """
        return [alias for alias in cls._linker._aux_cache.connectors.keys()]
