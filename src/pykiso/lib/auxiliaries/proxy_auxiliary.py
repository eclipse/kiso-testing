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
from typing import List, Optional, Tuple, Union

from pykiso import AuxiliaryInterface, CChannel
from pykiso.test_setup.config_registry import ConfigRegistry
from pykiso.test_setup.dynamic_loader import PACKAGE

log = logging.getLogger(__name__)


class ProxyAuxiliary(AuxiliaryInterface):
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
        """
        self.channel = com
        self.logger = ProxyAuxiliary._init_trace(activate_trace, trace_dir, trace_name)
        self.proxy_channels = self.get_proxy_con(aux_list)
        super().__init__(**kwargs)

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
        log.info(f"create proxy trace file at {log_path}")
        handler = logging.FileHandler(log_path, "w+")
        handler.setFormatter(log_format)
        # create logger and set the log level to DEBUG
        logger = logging.getLogger(f"{__name__}.PROXY")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        return logger

    def get_proxy_con(
        self, aux_list: List[Union[str, AuxiliaryInterface]]
    ) -> Tuple[AuxiliaryInterface]:
        """Retrieve all connector associated to all given existing Auxiliaries.

        If auxiliary alias exists but auxiliary instance was not created
        yet, create it immediately using ConfigRegistry _aux_cache.

        :param aux_list: list of auxiliary's alias

        :return: tuple containing all connectors associated to
            all given auxiliaries
        """
        channel_inst = []

        for aux in aux_list:
            # aux_list can contain a auxiliary instance just grab the
            # channel
            if isinstance(aux, AuxiliaryInterface):
                self._check_compatibility(aux)
                channel_inst.append(aux.channel)
                continue
            # check the system module in order to get the auxiliary
            # instance
            aux_inst = sys.modules.get(f"{PACKAGE}.auxiliaries.{aux}")
            if aux_inst is not None:
                self._check_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # check if the given aux_name is in the available aux
            # alias list
            elif aux in ConfigRegistry.get_auxes_alias():
                log.warning(
                    f"Auxiliary : {aux} is not using import magic mechanism (pre-loaded)"
                )
                # load it using ConfigRegistry _aux_cache
                aux_inst = ConfigRegistry._linker._aux_cache.get_instance(aux)
                self._check_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # the given auxiliary alias doesn't exist or refer to a
            # invalid one
            else:
                log.error(f"Auxiliary : {aux} doesn't exist")

        return tuple(channel_inst)

    @staticmethod
    def _check_compatibility(aux: AuxiliaryInterface) -> None:
        """Check if the given auxiliary is proxy compatible.

        :param aux: auxiliary instance to check

        :raises NotImplementedError: if is_proxy_capable flag is False
        """
        if not aux.is_proxy_capable:
            raise NotImplementedError(
                f"Auxiliary {aux} is not compatible with a proxy auxiliary"
            )

    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: if channel creation is successful return True otherwise false
        """
        try:
            log.info("Create auxiliary instance")
            log.info("Enable channel")
            self.channel.open()
            return True
        except Exception as e:
            log.exception(f"Error encouting during channel creation, reason : {e}")
            self.stop()
            return False

    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        try:
            log.info("Delete auxiliary instance")
            self.channel.close()
        except Exception as e:
            log.exception(f"Error encouting during channel closure, reason : {e}")
        finally:
            return True

    def _run_command(self) -> None:
        """Run all commands present in each proxy connectors queue in
        by sending it over current associated CChannel.

        In addition, all commands are dispatch to others auxiliaries
        using proxy connector queue out.
        """
        for conn in self.proxy_channels:
            if not conn.queue_in.empty():
                args, kwargs = conn.queue_in.get()
                message = kwargs.get("msg")
                if message is not None:
                    self._dispatch_command(
                        con_use=conn,
                        **kwargs,
                    )
                self.channel._cc_send(*args, **kwargs)

    def _dispatch_command(self, con_use: CChannel, **kwargs: dict):
        """Dispatch the current command to others connected auxiliaries.

        This action is performed by populating the queue out from each
        proxy connectors.

        :param con_use: current proxy connector where the command comes
            from
        :param kwargs: named arguments
        """
        for conn in self.proxy_channels:
            if conn != con_use:
                conn.queue_out.put(kwargs)

    def _abort_command(self) -> None:
        """Not Used."""
        return True

    def _receive_message(self, timeout_in_s: float = 0) -> None:
        """When no request are sent this method is called by AuxiliaryInterface run
        method. At each message received, this method will populate each
        proxy connectors queue out.

        :param timeout_in_s: maximum amount of time in second to wait
            for a message.
        """
        try:
            recv_response = self.channel.cc_receive(timeout=timeout_in_s, raw=True)
            received_data = recv_response.get("msg")
            # if data are received, populate connected proxy connectors
            # queue out
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

    def run(self) -> None:
        """Run function of the auxiliary thread"""
        while not self.stop_event.is_set():
            # Step 1: Check if a request is available & process it
            request = ""
            # Check if a request was received
            if not self.queue_in.empty():
                request = self.queue_in.get_nowait()
            # Process the request
            if request == "create_auxiliary_instance" and not self.is_instance:
                # Call the internal instance creation method
                return_code = self._create_auxiliary_instance()
                # Based on the result set status:
                self.is_instance = return_code
                # Enqueue the result for the request caller
                self.queue_out.put(return_code)
            elif request == "delete_auxiliary_instance" and self.is_instance:
                # Call the internal instance delete method
                return_code = self._delete_auxiliary_instance()
                # Based on the result set status:
                self.is_instance = not return_code
                # Enqueue the result for the request caller
                self.queue_out.put(return_code)
            elif request != "":
                # A request was received but could not be processed
                log.warning(f"Unknown request '{request}', will not be processed!")
                log.warning(f"Aux status: {self.__dict__}")

            # Step 2: Send stack command and propagate them to others connected auxiliaires
            # and check if something was received if instance was created
            if self.is_instance:
                self._run_command()
                self._receive_message(timeout_in_s=0)

        # Thread stop command was set
        log.info("{} was stopped".format(self))
        # Delete auxiliary external instance if not done
        if self.is_instance:
            self._delete_auxiliary_instance()
