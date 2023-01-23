##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Multiprocessing Proxy Auxiliary
*******************************

:module: mp_proxy_auxiliary

:synopsis: concrete implementation of a multiprocessing proxy auxiliary

This auxiliary simply spread all commands and received messages to all
connected auxiliaries. This auxiliary is only usable through mp proxy
connector.

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

.. currentmodule:: mp_proxy_auxiliary

"""
import collections
import logging
import multiprocessing
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from pykiso import AuxiliaryInterface, CChannel, MpAuxiliaryInterface
from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy
from pykiso.test_setup.config_registry import ConfigRegistry
from pykiso.test_setup.dynamic_loader import PACKAGE

TraceOptions = collections.namedtuple("TraceOptions", "activate dir name")

log = logging.getLogger(__name__)


class MpProxyAuxiliary(MpAuxiliaryInterface):
    """Proxy auxiliary for multi auxiliaries communication handling.

    ..note :: this auxiliary version is using the multiprocessing
        auxiliary interface.
    """

    def __init__(
        self,
        com: CChannel,
        aux_list: List[str],
        activate_trace: bool = False,
        trace_dir: Optional[str] = None,
        trace_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize attributes.

        :param com: Communication connector
        :param aux_list: list of auxiliary's alias
        :param activate_trace: True if the trace is activate otherwise
            False
        :param trace_dir: trace directory path (absolute or relative)
        :param trace_name: trace full name (without file extension)
        """
        self.channel = com
        self.trace_options = TraceOptions(
            activate=activate_trace, dir=trace_dir, name=trace_name
        )
        self.proxy_channels = self.get_proxy_con(aux_list)
        self.logger: logging.Logger = None
        self.aux_list = aux_list
        super().__init__(**kwargs)

    def _init_trace(
        self,
        logger: logging.Logger,
        activate: bool,
        t_dir: Optional[str] = None,
        t_name: Optional[str] = None,
    ) -> None:
        """Initialize the logging trace for proxy auxiliary received
        message recording and process debugging.

        :param logger: base logger where a FileHandler is added
        :param activate: True if the trace is activate otherwise False
        :param t_dir: trace directory path (absolute or relative)
        :param t_name: trace full name (without file extension)
        """

        if not activate:
            return None

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

        # configure the file handler and create the tarce file
        log_format = logging.Formatter("%(asctime)s : %(message)s")
        logger.info(f"create proxy trace file at {log_path}")
        handler = logging.FileHandler(log_path, "w+")
        handler.setFormatter(log_format)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    def get_proxy_con(self, aux_list: List[str]) -> Tuple[CCMpProxy]:
        """Retrieve all connector associated to all given existing Auxiliaries.

        If auxiliary alias exists but auxiliary instance was not created
        yet, create it immediately using ConfigRegistry _aux_cache.

        :param aux_list: list of auxiliary's alias

        :return: tuple containing all connectors associated to
            all given auxiliaries
        """
        channel_inst: List[CCMpProxy] = []

        for aux_name in aux_list:
            aux_inst = sys.modules.get(f"{PACKAGE}.auxiliaries.{aux_name}")
            if aux_inst is not None:
                self._check_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # check if the given aux_name is in the available aux
            # alias list
            elif aux_name in ConfigRegistry.get_auxes_alias():
                log.internal_warning(
                    f"Auxiliary : {aux_name} is not using import magic mechanism (pre-loaded)"
                )
                # load it using ConfigRegistry _aux_cache
                aux_inst = ConfigRegistry._linker._aux_cache.get_instance(aux_name)
                self._check_compatibility(aux_inst)
                channel_inst.append(aux_inst.channel)
            # the given auxiliary alias doesn't exist or refer to a
            # invalid one
            else:
                log.error(f"Auxiliary : {aux_name} doesn't exist")

        # Check if auxes/connectors are compatible with the proxy aux
        self._check_channels_compatibility(channel_inst)

        # Finally bind the physical channel to the proxy channels to
        # share its API to the user's auxiliaries
        for channel in channel_inst:
            channel._bind_channel_info(self)

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

    @staticmethod
    def _check_channels_compatibility(channels: List[CChannel]) -> None:
        """Check if all associated channels are compatible.

        :param channels: all channels collected by the proxy aux

        :raises TypeError: if the connector is not an instance of
            CCProxy
        """
        for channel in channels:
            if not isinstance(channel, CCMpProxy):
                raise TypeError(
                    f"Channel {channel} is not compatible! "
                    f"Expected a CCMpProxy instance, got {channel.__class__.__name__}"
                )

    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: if channel creation is successful return True otherwise false
        """
        try:
            self.logger.info("Create auxiliary instance")
            self.logger.info("Enable channel")
            self.channel.open()
            return True
        except Exception:
            self.logger.exception("Error encouting during channel creation")
            self.stop()
            return False

    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        try:
            self.logger.info("Delete auxiliary instance")
            self.channel.close()
            # in very rare case if a queue is populated, ITF could be
            # blocked in a infinite loop. This is a workaround, and not
            # the final implementation.
            self._empty_queue(self.queue_in)
            for conn in self.proxy_channels:
                self._empty_queue(conn.queue_in)
                self._empty_queue(conn.queue_out)
        except Exception:
            self.logger.exception("Error encouting during channel closure")

        return True

    @staticmethod
    def _empty_queue(queue: multiprocessing.Queue) -> None:
        """Empty a given queue by simply calling get until queue  is
        empty.

        :param queue: queue to clear
        """
        while not queue.empty():
            queue.get_nowait()

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

    def _receive_message(self, timeout_in_s: float = 0) -> None:
        """When no request are sent this method is called by
        AuxiliaryInterface run method. At each message received, this
        method will populate each proxy connectors queue out.

        :param timeout_in_s: maximum amount of time in second to wait
            for a message.
        """
        try:
            recv_response = self.channel.cc_receive(timeout=timeout_in_s)
            received_data = recv_response.get("msg")
            # if data are received, populate connected proxy connectors
            # queue out
            if received_data is not None:
                self.logger.debug(
                    f"raw data : {received_data.hex()} || channel : {self.channel.name}"
                )
                for conn in self.proxy_channels:
                    conn.queue_out.put(recv_response)
        except Exception:
            self.logger.exception(
                f"encountered error while receiving message via {self.channel}"
            )

    def run(self) -> None:
        """Run function of the auxiliary process."""
        # initialize logging mechanism at process startup
        self.initialize_loggers()
        # initialize trace for message recording
        self._init_trace(self.logger, *self.trace_options)

        while not self.stop_event.is_set():
            # Step 1: Check if a request is available & process it
            request = ""
            # Check if a request was received
            if not self.queue_in.empty():
                request = self.queue_in.get_nowait()
            # Process the request
            if request == "create_auxiliary_instance" and not self.is_instance:
                # Call the internal instance creation method
                self.is_instance = self._create_auxiliary_instance()
                # Enqueue the result for the request caller
                self.queue_out.put(self.is_instance)
            elif request == "delete_auxiliary_instance" and self.is_instance:
                # Call the internal instance delete method
                self.is_instance = not (self._delete_auxiliary_instance())
                # Enqueue the result for the request caller
                self.queue_out.put(self.is_instance)
            elif request != "":
                # A request was received but could not be processed
                self.logger.warning(
                    f"Unknown request '{request}', will not be processed!"
                )
            # Step 2: Send stack command and propagate them to others
            # connected auxiliaires and check if something was received
            # if instance was created
            if self.is_instance:
                self._run_command()
                self._receive_message(timeout_in_s=0)

            # Free up cpu usage when auxiliary is suspended
            if not self.is_instance:
                time.sleep(0.050)

        # Thread stop command was set
        self.logger.info("{} was stopped".format(self))
        # Delete auxiliary external instance if not done
        if self.is_instance:
            self._delete_auxiliary_instance()
