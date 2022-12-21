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
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type

from .dynamic_loader import DynamicImportLinker

if TYPE_CHECKING:
    from pykiso.auxiliary import AuxiliaryCommon
    from pykiso.types import (
        AuxiliaryAlias,
        AuxiliaryConfig,
        ConfigDict,
        ConnectorAlias,
        ConnectorConfig,
    )


class ConfigRegistry:
    """Register auxiliaries with connectors to provide systemwide import
    statements.

    Internally patch the user-configuration if multiple auxiliaries share
    a same communication channel.
    """

    _linker = None

    @staticmethod
    def _make_proxy_channel_config(
        aux_name: AuxiliaryConfig, multiprocessing: bool
    ) -> Tuple[ConnectorAlias, ConnectorConfig]:
        """Craft the configuration dictionary for a proxy communication
        channel to attach to the auxiliary instead of the 'physical' channel.

        :param aux_name: name of the auxiliary to which the proxy channel
            should be plugged.
        :param multiprocessing: whether the auxiliary is multiprocessing-
            based or thread-based.
        :return: the resulting proxy channel name and its configuration as
            as a tuple.
        """
        from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy
        from pykiso.lib.connectors.cc_proxy import CCProxy

        cchannel_class = CCProxy if not multiprocessing else CCMpProxy
        name = f"proxy_channel_{aux_name}"
        config = {
            "config": None,
            "type": f"{cchannel_class.__module__}:{cchannel_class.__name__}",
        }
        return name, config

    @staticmethod
    def _make_proxy_aux_config(
        channel_name: ConnectorAlias,
        aux_list: List[AuxiliaryAlias],
        multiprocessing: bool,
    ) -> Tuple[AuxiliaryAlias, AuxiliaryConfig]:
        """Craft the configuration dictionary for a proxy auxiliary to be
        attached to all auxiliaries sharing a communication channel.

        :param channel_name: name of the 'physical' channel that should
            be attached to the proxy auxiliary (the only direct connection).
        :param multiprocessing: whether the communication channel is
            multiprocessing-based or thread-based.
        :return: the resulting proxy auxiliary name and its configuration as
            as a tuple.
        """
        from pykiso.lib.auxiliaries.mp_proxy_auxiliary import MpProxyAuxiliary
        from pykiso.lib.auxiliaries.proxy_auxiliary import ProxyAuxiliary

        aux_class = ProxyAuxiliary if not multiprocessing else MpProxyAuxiliary
        name = f"proxy_aux_{channel_name}"
        config = {
            "connectors": {"com": channel_name},
            "config": {"aux_list": aux_list},
            "type": f"{aux_class.__module__}:{aux_class.__name__}",
        }
        return name, config

    @staticmethod
    def _link_cchannel_to_auxiliaries(
        config: ConfigDict,
    ) -> Dict[ConnectorAlias, List[AuxiliaryAlias]]:
        """Go through each auxiliary configuration, link each found
        channel name to the auxiliary(s) that hold it.

        :param config: dictionary containing yaml configuration content
        :return: a dictionary linking each channel name to the list of
            auxiliaries that are connected to the channel.
        """
        cchannel_to_auxiliaries = defaultdict(list)
        for auxiliary, aux_details in config["auxiliaries"].items():
            try:
                cchannel = aux_details["connectors"]["com"]
            except KeyError:
                # auxiliary doesn't have a communication channel attached
                continue

            cchannel_to_auxiliaries[cchannel].append(auxiliary)
        return cchannel_to_auxiliaries

    @classmethod
    def register_aux_con(cls, config: ConfigDict) -> None:
        """Create import hooks. Register auxiliaries and connectors.

        :param config: dictionary containing yaml configuration content
        """
        # 1. Detect required proxy setups
        cchannel_to_auxiliaries = cls._link_cchannel_to_auxiliaries(config)
        proxies = []

        # 2. Overwrite auxiliary and connector config with required proxies
        for channel_name, auxiliaries in cchannel_to_auxiliaries.items():
            if len(auxiliaries) < 2:
                # only one auxiliary holds the channel so there's nothing to patch
                continue

            # detect if communication channel is multiprocessing-based
            mp_enabled = False
            if config["connectors"][channel_name].get("config") is not None:
                mp_enabled = config["connectors"][channel_name]["config"].get(
                    "processing", False
                )

            # create a proxy auxiliary config for this shared channel
            proxy_aux_name, proxy_aux_cfg = cls._make_proxy_aux_config(
                channel_name, auxiliaries, mp_enabled
            )
            config["auxiliaries"][proxy_aux_name] = proxy_aux_cfg
            proxies.append(proxy_aux_name)

            # create a proxy channel config for each of the auxiliaries sharing the channel
            for aux_name in auxiliaries:
                cc_proxy_name, cc_proxy_cfg = cls._make_proxy_channel_config(
                    aux_name, mp_enabled
                )
                config["auxiliaries"][aux_name]["connectors"]["com"] = cc_proxy_name
                config["connectors"][cc_proxy_name] = cc_proxy_cfg

        # 3. Create and install the auxiliary import hook
        cls._linker = DynamicImportLinker()
        cls._linker.install()

        # 4. Provide auxiliaries and connectors from potentially patched configuration
        for connector, con_details in config["connectors"].items():
            cfg = con_details.get("config") or dict()
            cls._linker.provide_connector(connector, con_details["type"], **cfg)

        for auxiliary, aux_details in config["auxiliaries"].items():
            cfg = aux_details.get("config") or dict()
            cls._linker.provide_auxiliary(
                auxiliary,
                aux_details["type"],
                aux_cons=aux_details.get("connectors") or dict(),
                **cfg,
            )

        # 5. Finally, import required ProxyAuxiliary instances so that user doesn't have to
        for proxy_aux in proxies:
            cls._linker._aux_cache.get_instance(proxy_aux)

    @classmethod
    def delete_aux_con(cls) -> None:
        """Deregister the import hooks, close all running threads,
        delete all instances.
        """
        cls._linker.uninstall()

    @classmethod
    def get_all_auxes(cls) -> Dict[AuxiliaryAlias, AuxiliaryCommon]:
        """Return all auxiliaires instances and alias

        :return: dictionary with alias as keys and instances as values
        """
        return cls._linker._aux_cache.instances

    @classmethod
    def get_auxes_by_type(
        cls, aux_type: Type[AuxiliaryCommon]
    ) -> Dict[str, AuxiliaryCommon]:
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
    def get_aux_by_alias(cls, alias: AuxiliaryAlias) -> AuxiliaryCommon:
        """Return the associated auxiliary instance to the given alias.

        :param alias: auxiliary's alias
        :return: auxiliary instance created by the dymanic loader
        """
        return cls._linker._aux_cache.get_instance(alias)

    @classmethod
    def get_aux_config(cls, name: AuxiliaryAlias) -> AuxiliaryConfig:
        """Return the registered auxiliary configuration based on his
        name.

        :param name: auxiliary's alias
        :return: auxiliary's configuration (yaml content)
        """
        return cls._linker._aux_cache.configs[name]

    @classmethod
    def get_auxes_alias(cls) -> List[AuxiliaryAlias]:
        """return all created auxiliaries alias.

        :return: list containing all auxiliaries alias
        """
        return [alias for alias in cls._linker._aux_cache.connectors.keys()]
