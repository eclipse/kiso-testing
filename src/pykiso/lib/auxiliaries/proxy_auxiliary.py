##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Proxy Auxiliary
***************

:module: proxy_auxiliary

:synopsis: auxiliary use to connect multiple auxiliaries on a unique connector.

This auxiliary simply spread all commands and received messages to all connected
auxiliaries. This auxiliary is only usable through proxy connector.

.. code-block:: none

     ___________   ___________         ___________
    |           | |           | ..... |           |
    |   Aux 1   | |   Aux 1   |       |   Aux n   |
    |___________| |___________|       |___________|
          |             |                   |
          |             |                   |
     ___________   ___________         ___________
    |           | |           | ..... |           |
    |Proxy_con 1| |Proxy_con 2|       |Proxy_con n|
    |___________| |___________|       |___________|
          |             |                   |
          |             |                   |
          |             |                   |
     _____________________________________________
    |                                             |
    |               Proxy Auxiliary               |
    |_____________________________________________|
                        |
                        |
     _____________________________________________
    |                                             |
    |               Connector Channel             |
    |_____________________________________________|

.. currentmodule:: proxy_auxiliary

"""

import logging
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from pykiso import AuxiliaryInterface, CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
    open_connector,
)
from pykiso.lib.connectors.cc_proxy import CCProxy
from pykiso.test_setup.config_registry import ConfigRegistry
from pykiso.test_setup.dynamic_loader import PACKAGE

log = logging.getLogger(__name__)


class ProxyAuxiliary(DTAuxiliaryInterface):
    """Proxy auxiliary for multi auxiliaries communication handling."""

    def __init__(
        self,
        com: CChannel,
        aux_list: List[str],
        activate_trace: bool = False,
        trace_dir: Optional[str] = None,
        trace_name: Optional[str] = None,
        **kwargs,
    ):
        """Initialize attributes.

        :param com: Communication connector
        :param aux_list: list of auxiliary's alias
        :param activate_trace: log all received messages in a
            dedicated trace file or not
        :param trace_dir: where to place the trace
        :param trace_name: trace's file name
        """
        super().__init__(
            is_proxy_capable=True, tx_task_on=False, rx_task_on=True, **kwargs
        )
        self.channel = com
        self.logger = self._init_trace(activate_trace, trace_dir, trace_name)
        self.proxy_channels = self.get_proxy_con(aux_list)

    @staticmethod
    def _init_trace(
        activate: bool, t_dir: Optional[str] = None, t_name: Optional[str] = None
    ) -> logging.Logger:
        """Initialize the logging trace for proxy auxiliary received
        message recording.

        :param activate: True if the trace is activate otherwise False
        :param t_dir: trace directory path (absolute or relative)
        :param t_name: trace full name (without file extension)

        :return : created logger containing the configured
            FileHander otherwise default logger
        """
        logger = log

        if not activate:
            return logger

        # Just avoid the case the given trace directory is None
        t_dir = "" if t_dir is None else t_dir
        # if the given log path is not absolute add root path
        # (where pykiso is launched) otherwise take it as it is
        dir_path = (
            (Path() / t_dir).resolve() if not Path(t_dir).is_absolute() else Path(t_dir)
        )
        # if no specific logging file name is given take the default one
        t_name = (
            time.strftime(f"%Y-%m-%d_%H-%M-%S_{t_name}.log")
            if t_name is not None
            else time.strftime("%Y-%m-%d_%H-%M-%S_proxy_logging.log")
        )
        # if path doesn't exists take root path (where pykiso is launched)
        log_path = (
            dir_path / t_name if dir_path.exists() else (Path() / t_name).resolve()
        )

        # configure the file handler and create the trace file
        log_format = logging.Formatter("%(asctime)s : %(message)s")
        log.internal_info(f"create proxy trace file at {log_path}")
        handler = logging.FileHandler(log_path, "w+")
        handler.setFormatter(log_format)
        # create logger and set the log level to DEBUG
        logger = logging.getLogger(f"{__name__}.PROXY")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        return logger

    def get_proxy_con(self, aux_list: List[str]) -> Tuple[CCProxy, ...]:
        """Retrieve all connector associated to all given existing Auxiliaries.

        If auxiliary alias exists but auxiliary instance was not created
        yet, create it immediately using ConfigRegistry _aux_cache.

        :param aux_list: list of auxiliary's alias

        :return: tuple containing all connectors associated to
            all given auxiliaries
        """
        channel_inst: List[CCProxy] = []

        for aux in aux_list:
            # aux_list can contain a auxiliary instance just grab the
            # channel
            if isinstance(aux, (AuxiliaryInterface, DTAuxiliaryInterface)):
                self._check_aux_compatibility(aux)
                channel_inst.append(aux.channel)
                continue
            # check the system module in order to get the auxiliary
            # instance
            aux_inst = sys.modules.get(f"{PACKAGE}.auxiliaries.{aux}")
            if aux_inst is not None:
                self._check_aux_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # check if the given aux_name is in the available aux
            # alias list
            elif aux in ConfigRegistry.get_auxes_alias():
                log.internal_info(
                    f"Auxiliary '{aux}' is not using import magic mechanism (pre-loaded)"
                )
                # load it using ConfigRegistry _aux_cache
                aux_inst = ConfigRegistry.get_aux_by_alias(aux)
                self._check_aux_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # the given auxiliary alias doesn't exist or refer to a
            # invalid one
            else:
                log.error(f"Auxiliary '{aux}' doesn't exist")

        # Check if auxes/connectors are compatible with the proxy aux
        self._check_channels_compatibility(channel_inst)

        # Finally bind the physical channel to the proxy channels to
        # share its API to the user's auxiliaries
        for channel in channel_inst:
            channel._bind_channel_info(self)

        return tuple(channel_inst)

    @staticmethod
    def _check_aux_compatibility(aux) -> None:
        """Check if the given auxiliary is proxy compatible.

        :param aux: auxiliary instance to check

        :raises NotImplementedError: if is_proxy_capable flag is False
        """
        if not aux.is_proxy_capable:
            raise NotImplementedError(
                f"Auxiliary {aux} is not compatible with a proxy auxiliary!"
            )

    @staticmethod
    def _check_channels_compatibility(channels: List[CChannel]) -> None:
        """Check if all associated channels are compatible.

        :param channels: all channels collected by the proxy aux

        :raises TypeError: if the connector is not an instance of
            CCProxy
        """
        for channel in channels:
            if not isinstance(channel, CCProxy):
                raise TypeError(f"Channel {channel} is not compatible!")

    def _dispatch_tx_method_to_channels(self) -> None:
        """Attached public run_command method to all connected proxy
        channels.

        .. note:: This method use the thread safe method implemented by
            each proxy channels(attached_tx_callback).
        """
        for conn in self.proxy_channels:
            conn.attach_tx_callback(self.run_command)

    @open_connector
    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel and dispatch tx method.

        :return: if channel creation is successful return True otherwise
            False
        """
        self._dispatch_tx_method_to_channels()
        log.internal_info("Auxiliary instance created")
        return True

    @close_connector
    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: if channel deletion is successful return True otherwise
            False
        """
        log.internal_info("Auxiliary instance deleted")
        return True

    def run_command(self, conn: CChannel, *args: tuple, **kwargs: dict) -> None:
        """Transmit an incoming request from a linked proxy channel
        to the proxy auxiliary's channel.

        :param conn: current proxy channel instance which the command
            comes from
        :param args: postional arguments
        :param args: named arguments
        """
        with self.lock:
            self._run_command(conn, *args, **kwargs)

    def _run_command(self, conn: CChannel, *args: tuple, **kwargs: dict) -> None:
        """Send the request coming from the given proxy channel and
        dispatch it to the other linked proxy channels.

        :param conn: current proxy channel instance which the command
            comes from
        :param args: postional arguments
        :param args: named arguments

        In addition, all commands are dispatch to others auxiliaries
        using proxy connector queue out.
        """
        self.channel.cc_send(*args, **kwargs)
        self._dispatch_command(con_use=conn, **kwargs)

    def _dispatch_command(self, con_use: CChannel, **kwargs: dict):
        """Dispatch the current command to others connected auxiliaries.

        This action is performed by populating the queue out from each
        proxy connectors.

        :param con_use: current proxy channel instance which the command
            comes from
        :param kwargs: named arguments
        """
        for conn in self.proxy_channels:
            if conn != con_use:
                conn.queue_out.put(kwargs)

    def _receive_message(self, timeout_in_s: float = 0) -> None:
        """Get a message from the associated channel and dispatch it to
        the liked proxy channels.

        .. note:: this method is called by the rx thread task from the
            inherit interface class


        :param timeout_in_s: maximum amount of time (seconds) to wait
            for a message
        """
        try:
            recv_response = self.channel.cc_receive(timeout=timeout_in_s)
            received_data = recv_response.get("msg")
            # if data are received, populate connector's queue_out
            if received_data is not None:
                self.logger.debug(
                    f"received response : data {received_data.hex()} || channel : {self.channel.name}"
                )
                for conn in self.proxy_channels:
                    conn.queue_out.put(recv_response)
        except Exception:
            log.exception(
                f"encountered error while receiving message via {self.channel}"
            )
