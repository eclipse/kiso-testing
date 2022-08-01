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

from uds import Config, Uds

from pykiso.connector import CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface

log = logging.getLogger(__name__)


class UdsBaseAuxiliary(DTAuxiliaryInterface):
    """Base Auxiliary class for handling UDS protocol."""

    POSITIVE_RESPONSE_OFFSET = 0x40

    def __init__(
        self,
        com: CChannel,
        odx_file_path: Optional[Union[Path, str]] = None,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
        tp_layer: dict = None,
        uds_layer: dict = None,
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
        self.req_id = tp_layer.get("req_id")
        self.res_id = tp_layer.get("res_id")
        self.uds_config_enable = False
        self.uds_config = None
        self.layer_config = (tp_layer, uds_layer)

        super().__init__(
            is_proxy_capable=True, tx_task_on=False, rx_task_on=True, **kwargs
        )

    @open_connector
    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: if channel creation is successful return True
            otherwise false
        """
        try:
            tp_conf, uds_conf = self.layer_config
            Config.load_com_layer_config(tp_conf, uds_conf)

            self.uds_config = Uds(
                self.odx_file_path,
                connector=self.channel,
                reqId=self.req_id,
                resId=self.res_id,
            )

            if hasattr(self, "transmit"):
                self.uds_config.tp.overwrite_transmit_method(self.transmit)
            if hasattr(self, "receive"):
                self.uds_config.tp.overwrite_receive_method(self.receive)
            return True
        except Exception:
            log.exception("An error occurred during kiso-python-uds initialization")
            return False

    @close_connector
    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        log.info("Auxiliary instance deleted")
        return True
