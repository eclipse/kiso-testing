##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS Auxiliary acting as a Server/ECU
************************************

:module: uds_server_auxiliary

:synopsis: Auxiliary used to handle Unified Diagnostic Service protocol as a Server.
    This auxiliary is meant to run in the background and replies to configured requests.

.. currentmodule:: uds_auxiliary

"""
from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Union

from uds import IsoServices

from .common.odx_parser import OdxParser
from .common.uds_base_auxiliary import UdsBaseAuxiliary
from .common.uds_callback import UdsCallback

log = logging.getLogger(__name__)

# possible data lengths for CAN FD padding
CAN_FD_DATA_LENGTHS = (8, 12, 16, 20, 24, 32, 48, 64)


class UdsServerAuxiliary(UdsBaseAuxiliary):
    """Auxiliary used to handle the UDS protocol on server (ECU) side."""

    CAN_FD_PADDING_PATTERN = 0xCC
    services = IsoServices

    def __init__(self, **kwargs):
        """Initialize attributes.

        :param com: communication channel connector.
        :param config_ini_path: uds parameters file.
        :param request_id: optional CAN ID used for sending messages.
        :param response_id: optional CAN ID used for receiving messages.
        :param odx_file_path: ecu diagnostic definition file.
        """
        super().__init__(**kwargs)

        self._ecu_config = None
        if self.odx_file_path is not None:
            self._ecu_config = OdxParser(self.odx_file_path).parse()

        self._callbacks: Dict[str, UdsCallback] = {}
        self._callback_lock = threading.Lock()

    @property
    def callbacks(self):
        """Access the callback dictionary in a thread-safe way.

        :return: the internal callbacks dictionary.
        """
        with self._callback_lock:
            return self._callbacks

    @staticmethod
    def format_data(uds_data: List[int]) -> str:
        """Format UDS data as a list of integers to a hexadecimal string.

        :param uds_data: UDS data as a list of integers.

        :return: the UDS data as a hexadecimal string.
        """
        return f"0x{bytes(uds_data).hex().upper()}"

    @classmethod
    def _pad_message(cls, message: List[int]) -> List[int]:
        """Pad a CAN FD message to send with the configured padding pattern.

        :param message: message to pad.

        :return: the padded message.
        """
        padded_length = next(
            size for size in CAN_FD_DATA_LENGTHS if size >= len(message)
        )
        return message + ([cls.CAN_FD_PADDING_PATTERN] * (padded_length - len(message)))

    def transmit(
        self, data: List[int], req_id: Optional[int] = None, extended: bool = False
    ) -> None:
        """Pad and transmit a message through ITF connector. This method
        is also used as a substitute to the transmit method present in
        python-uds package.

        :param data: data to send.
        :param req_id: CAN message identifier. If not set use the one
            configured.
        :param extended: True if addressing mode is extended otherwise
            False.
        """
        req_id = req_id or self.req_id
        data = self._pad_message(data)
        self.channel._cc_send(msg=data, remote_id=req_id, raw=True)

    def receive(self) -> bytes:
        """Receive a message through ITF connector. Called inside a thread,
        this method is a substitute to the reception method used in the
        python-uds package.

        :param data: data to send
        :param req_id: CAN message identifier
        :param extended: True if addressing mode is extended otherwise
            False
        """
        received_data, arbitration_id = self.channel._cc_receive(timeout=0, raw=True)
        if received_data is not None and arbitration_id == self.res_id:
            return received_data

    def send_response(self, response_data) -> None:
        """Encode and transmit a UDS response.

        :param response_data: the UDS response to send.
        """
        to_send = self.uds_config.tp.encode_isotp(
            response_data, use_external_snd_rcv_functions=True
        )
        if to_send is not None:
            self.transmit(to_send, req_id=self.req_id)

    @staticmethod
    def encode_stmin(stmin: float) -> int:
        """Encode the provided minimum separation time according to the ISO TP
        specification.

        :param stmin: minimum separation time in ms.
        :raises ValueError: if the provided value is not valid.
        :return: the encoded STmin to be sent in a flow control frame.
        """
        if stmin == 0:
            return stmin
        elif 1 <= stmin <= 127:
            # 1 - 127 ms -> 0x01 - 0x7F
            return int(stmin)
        elif 0.1 <= stmin <= 0.9:
            # 0.1 - 0.9 ms -> 0xF1 - 0xF9
            return 0xF0 + int(stmin * 10)
        else:
            raise ValueError(
                f"Invalid minimum Separation Time {stmin}ms. "
                "Acceptable values are between 0.1ms and 127ms."
            )

    def send_flow_control(
        self, flow_status: int = 0, block_size: int = 0, stmin: float = 0
    ) -> None:
        """Send an ISO TP flow control frame to the client.

        :param flow_status: status of the flow control, defaults to 0
            (continue to send).
        :param block_size: size of the data block to send, defaults to 0
            (infinitely large).
        :param stmin: minimum separation time between 2 consecutive frames
            in ms, defaults to 0 ms.
        """
        flow_control_frame = [
            (0x30 + flow_status),
            block_size,
            self.encode_stmin(stmin),
        ]
        self.transmit(flow_control_frame)

    def register_callback(
        self,
        request: Union[int, List[int], UdsCallback],
        response: Optional[Union[int, List[int]]] = None,
        response_data: Optional[Union[int, bytes]] = None,
        data_length: Optional[int] = None,
    ) -> None:
        """Register an automatic response to send if the specified request is received
        from the client.

        The callback is stored inside the callbacks dictionary under the format
        `{"0x2EC4": UdsCallback()}`_, where the keys are case-sensitive and
        correspond to the registered requests.

        :param request: UDS request to be responded to.
        :param response: full UDS response to send. If not set, respond with a basic
            positive response with the specified response_data.
        :param response_data: UDS data to send. If not set, respond with a basic
            positive response containing no data.
        :param data_length: optional length of the data to send if it is supposed
            to have a fixed length (zero-padded).
        """
        callback = (
            request
            if isinstance(request, UdsCallback)
            else UdsCallback(
                request=request,
                response=response,
                response_data=response_data,
                data_length=data_length,
            )
        )
        self.callbacks[self.format_data(callback.request)] = callback

    def _receive_message(self, timeout_in_s: float) -> None:
        """Reception method called by the auxiliary thread. This method received
        data and triggers the registered callbacks according to the received data.

        :param timeout_in_s: timeout on reception.
        """
        received_data, arbitration_id = self.channel.cc_receive(timeout_in_s, raw=True)
        if received_data is not None and arbitration_id == self.res_id:
            try:
                uds_data = self.uds_config.tp.decode_isotp(
                    received_data=received_data, use_external_snd_rcv_functions=True
                )
                log.debug(
                    "Received ISO TP data: %s || UDS data: %s",
                    f"0x{received_data.hex()}",
                    self.format_data(uds_data),
                )
            except Exception as e:
                # avoid timeouts that would break the thread
                log.exception(e)
                return

            self._dispatch_callback(uds_data)

    def _dispatch_callback(self, received_uds_data: List[int]) -> None:
        """Verify if the received UDS request has an associated response
        registered by a callback and send it.

        :param received_uds_data: received UDS request from the client.
        """
        if self.uds_config_enable:
            service_id = received_uds_data[0]
            service_config = self._ecu_config.get(service_id)
            for service_subconfig in service_config:
                if received_uds_data == service_subconfig["request"]:
                    self.send_response(service_subconfig["response"])
        else:
            for callback in self.callbacks.values():
                # match on the registered request instead of the entire received request
                if callback.request == received_uds_data[: len(callback.request)]:
                    callback_to_execute = callback
                    break
            else:
                log.warning(
                    f"Unregistered request received: {self.format_data(received_uds_data)}"
                )
                return

        callback_to_execute(received_uds_data, self)
        return

    def _abort_command(self) -> None:
        """Not used, satisfy interface."""
        pass

    def _run_command(self, cmd_message, cmd_data=None) -> None:
        """Not used, satisfy interface."""
        pass
