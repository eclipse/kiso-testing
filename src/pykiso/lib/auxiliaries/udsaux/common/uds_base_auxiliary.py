##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
uds_base_auxiliary
******************

:module: uds_base_auxiliary

:synopsis: Auxiliary base class providing common methods for
    Unified Diagnostic Service protocol handling.
    This base auxiliary is not meant to be used directly, use its
    subclasses instead.

.. currentmodule:: uds_base_auxiliary

"""
import configparser
import logging
from pathlib import Path
from typing import Optional, Union

from uds import Uds, createUdsConnection

from pykiso.connector import CChannel
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface

log = logging.getLogger(__name__)


class UdsBaseAuxiliary(AuxiliaryInterface):
    """Base Auxiliary class for handling UDS protocol."""

    POSITIVE_RESPONSE_OFFSET = 0x40

    def __init__(
        self,
        com: CChannel,
        config_ini_path: Union[Path, str],
        odx_file_path: Optional[Union[Path, str]] = None,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
        **kwargs,
    ):
        """Initialize attributes.

        :param com: communication channel connector.
        :param config_ini_path: UDS parameter file.
        :param odx_file_path: ecu diagnostic definition file.
        :param request_id: optional CAN ID used for sending messages.
        :param response_id: optional CAN ID used for receiving messages.
        """
        self.channel = com
        self.odx_file_path = odx_file_path
        if odx_file_path:
            self.odx_file_path = Path(odx_file_path)

        self.config_ini_path = Path(config_ini_path)

        config = configparser.ConfigParser()
        config.read(self.config_ini_path)

        self.req_id = request_id or int(config.get("can", "defaultReqId"), 16)
        self.res_id = response_id or int(config.get("can", "defaultResId"), 16)

        self.uds_config_enable = False
        self.uds_config = None

        super().__init__(is_proxy_capable=True, **kwargs)

    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: if channel creation is successful return True
            otherwise false
        """
        try:
            log.info("Create auxiliary instance")
            log.info("Enable channel")
            self.channel.open()

            channel_name = self.channel.__class__.__name__.lower()

            if "vectorcan" in channel_name:
                interface = "vector"
                bus = self.channel.bus
            elif "pcan" in channel_name:
                interface = "peak"
                bus = self.channel.bus
            elif "socketcan" in channel_name:
                interface = "socketcan"
                bus = self.channel.bus
            elif "ccproxy" in channel_name:
                # Just fake python-uds (when proxy auxiliary is used),
                # by setting bus to True no channel creation is
                # performed
                bus = True
                interface = "peak"

            if self.odx_file_path:
                log.info("Create Uds Config connection with ODX")
                self.uds_config_enable = True
                self.uds_config = createUdsConnection(
                    self.odx_file_path,
                    "",
                    configPath=self.config_ini_path,
                    bus=bus,
                    interface=interface,
                    reqId=self.req_id,
                    resId=self.res_id,
                )
            else:
                log.info("Create Uds Config connection without ODX")
                self.uds_config_enable = False
                self.uds_config = Uds(
                    configPath=self.config_ini_path,
                    bus=bus,
                    interface=interface,
                    reqId=self.req_id,
                    resId=self.res_id,
                )
            if hasattr(self, "transmit"):
                self.uds_config.tp.overwrite_transmit_method(self.transmit)
            if hasattr(self, "receive"):
                self.uds_config.tp.overwrite_receive_method(self.receive)
            return True
        except Exception:
            log.exception("Error during channel creation")
            self.stop()
            return False

    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        log.info("Delete auxiliary instance")
        self.uds_config.disconnect()
        self.channel.close()
        return True
