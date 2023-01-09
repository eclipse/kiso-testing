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
import logging
import warnings
from pathlib import Path
from typing import Optional, Union

from uds import Config, Uds

from pykiso.connector import CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)

log = logging.getLogger(__name__)


class UdsBaseAuxiliary(DTAuxiliaryInterface):
    """Base Auxiliary class for handling UDS protocol."""

    POSITIVE_RESPONSE_OFFSET = 0x40
    DEFAULT_UDS_CONFIG = {
        "transport_protocol": "CAN",
        "p2_can_client": 5,
        "p2_can_server": 1,
    }
    DEFAULT_TP_CONFIG = {
        "addressing_type": "NORMAL",
        "n_sa": 0xFF,
        "n_ta": 0xFF,
        "n_ae": 0xFF,
        "m_type": "DIAGNOSTICS",
        "discard_neg_resp": False,
    }

    def __init__(
        self,
        com: CChannel,
        config_ini_path: Optional[Union[Path, str]] = None,
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
        super().__init__(
            is_proxy_capable=True, tx_task_on=False, rx_task_on=True, **kwargs
        )
        self.channel = com
        self.odx_file_path = odx_file_path
        self.req_id = request_id
        self.res_id = response_id
        self.uds_config_enable = False
        self.uds_config = None
        self.tp_layer = None
        self.tp_waiting_time = 0.010
        self.uds_layer = None
        self._init_com_layers(tp_layer, uds_layer)

        # remove it after a few releases just warn users
        if config_ini_path is not None:
            warnings.warn(
                "The usage of ini file is deprecated, nothing will be read from it",
                category=FutureWarning,
            )
            log.warning(
                f"apply following values for ISOTP layer configuration : {UdsBaseAuxiliary.DEFAULT_TP_CONFIG}"
            )
            log.warning(
                f"apply following values for UDS layer configuration : {UdsBaseAuxiliary.DEFAULT_UDS_CONFIG}"
            )

    def _init_com_layers(
        self, tp_layer: Optional[dict] = None, uds_layer: Optional[dict] = None
    ) -> None:
        """Initialize isotp and uds layer attributes.

        :param tp_layer: isotp configuration given at yaml level
        :param uds_layer: uds configuration given at yaml level
        """
        tp_layer = tp_layer or UdsBaseAuxiliary.DEFAULT_TP_CONFIG
        uds_layer = uds_layer or UdsBaseAuxiliary.DEFAULT_UDS_CONFIG
        # add configured request id and response id to tp layer config
        tp_layer["req_id"] = self.req_id
        tp_layer["res_id"] = self.res_id
        self.tp_layer = tp_layer
        self.uds_layer = uds_layer

    @open_connector
    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: if channel creation is successful return True
            otherwise false
        """

        try:
            is_not_none = self.odx_file_path is not None
            is_not_bool = not isinstance(self.odx_file_path, bool)

            if is_not_none and is_not_bool and Path(self.odx_file_path).exists():
                self.uds_config_enable = True
            else:
                self.odx_file_path = None

            Config.load_com_layer_config(self.tp_layer, self.uds_layer)
            self.uds_config = Uds(
                self.odx_file_path,
                connector=self.channel,
            )
            if hasattr(self, "transmit"):
                self.uds_config.overwrite_transmit_method(self.transmit)
            if hasattr(self, "receive"):
                self.uds_config.overwrite_receive_method(self.receive)
            return True
        except Exception:
            log.exception("An error occurred during kiso-python-uds initialization")
            return False

    @close_connector
    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        log.internal_info("Auxiliary instance deleted")
        return True
