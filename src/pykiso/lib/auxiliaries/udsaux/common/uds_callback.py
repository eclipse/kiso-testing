##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Helper classes for UDS callback registration
********************************************

:module: uds_callback

:synopsis: This module defines classes for the definition of
    UDS callbacks to be registered by the
    :py:class:`~pykiso.lib.auxiliaries.uds_aux.uds_server_auxiliary.UdsServerAuxiliary`_
    along with callbacks for functional requests (TransferData service).

.. currentmodule:: uds_callback

"""

from __future__ import annotations

import itertools
import logging
import time
import typing
from dataclasses import dataclass
from typing import Callable, ClassVar, List, Optional, Tuple, Union

from uds import IsoServices

if typing.TYPE_CHECKING:
    from pykiso.lib.auxiliaries.udsaux import UdsServerAuxiliary


log = logging.getLogger(__name__)


@dataclass
class UdsCallback:
    """Class used to store information in order to configure and send
    a response to the specified UDS request.

    :param request: request from the client that should be responded to.
    :param response: full UDS response to send. If not set, respond with a basic
        positive response with the specified response_data.
    :param response_data: UDS data to send. If not set, respond with a basic
        positive response containing no data.
    :param data_length: optional length of the data to send in the response if
        the data has a fixed length (zero-padded).
    :param callback: custom callback function to register. The callback function
        must have two positional arguments: the received request as a list of
        integers and the UdsServerAuxiliary instance.
    """

    # e.g. 0x1003 or [0x10, 0x03]
    request: Union[int, List[int]]
    # e.g. 0x5003 or [0x50, 0x03]
    response: Optional[Union[int, List[int]]] = None
    # e.g. 0x1011 or b'DATA'
    response_data: Optional[Union[int, bytes]] = None
    # specify zero-padding
    data_length: Optional[int] = None
    # custom callback
    callback: Optional[Callable[[List[int], UdsServerAuxiliary], None]] = None

    def __post_init__(self):
        """Parse the provided parameters to create a fully formed UDS response."""
        self.call_count = 0

        if isinstance(self.request, int):
            self.request = list(UdsCallback.int_to_bytes(self.request))

        if isinstance(self.response, int):
            self.response = list(UdsCallback.int_to_bytes(self.response))
        elif not self.response:
            self.response = [self.request[0] + 0x40] + self.request[1:]

        if self.response_data:
            self.response_data = (
                list(UdsCallback.int_to_bytes(self.response_data))
                if isinstance(self.response_data, int)
                else list(self.response_data)
            )
            self.response.extend(self.response_data)

        if self.data_length is not None and self.response_data:
            # pad with zeros to reach the expected length
            self.response.extend([0x00] * (self.data_length - len(self.response_data)))

    def __call__(self, received_request: List[int], aux: UdsServerAuxiliary) -> None:
        """Trigger the callback and increase the call count.

        If a custom callback function is defined call it, otherwise send
        the registered response to the client.

        :param received_request: the received UDS request as a list of
            integers
        :param aux: the UdsServerAuxiliary instance for which the
            callback is registered
        """
        self.call_count += 1
        if self.callback is not None:
            self.callback(received_request, aux)
        else:
            aux.send_response(self.response)

    @staticmethod
    def int_to_bytes(integer: int) -> bytes:
        return integer.to_bytes((integer.bit_length() + 7) // 8, "big")


@dataclass
class UdsDownloadCallback(UdsCallback):
    """UDS Callback for DownloadData handling on server-side."""

    MAX_TRANSFER_SIZE: ClassVar[int] = 0xFFFF
    request: Union[int, List[int]] = IsoServices.RequestDownload
    stmin: float = 0

    def __post_init__(self):
        super().__post_init__()
        self.callback = self.handle_data_download
        self.transfer_successful = False

    @staticmethod
    def get_download_data_transfer_size(download_request: List[int]) -> int:
        addr_len_format_identifier_index = 2
        address_and_length_format_identifier = download_request[
            addr_len_format_identifier_index
        ]
        nb_bytes_memory_address_param = address_and_length_format_identifier & 0x0F
        nb_bytes_memory_size_param = address_and_length_format_identifier >> 4
        data_size_start_index = (
            addr_len_format_identifier_index + nb_bytes_memory_address_param + 1
        )
        data_size_end_index = data_size_start_index + nb_bytes_memory_size_param + 1

        memory_size = download_request[data_size_start_index:data_size_end_index]
        data_transfer_size = int.from_bytes(bytes(memory_size), byteorder="big") - 1
        return data_transfer_size

    @staticmethod
    def get_first_frame_data_length(first_frame: List[int]) -> Tuple[int, int]:
        first_frame_data_len = (first_frame[0] & 0x0F) + first_frame[1]
        uds_data_start_index = 2
        if first_frame_data_len == 0:
            uds_data_start_index = 6
            first_frame_data_len = int.from_bytes(bytes(first_frame[2:6]), "big")
        return first_frame_data_len, uds_data_start_index

    def make_request_download_response(self, max_transfer_size: int = None):
        max_transfer_size = max_transfer_size or self.MAX_TRANSFER_SIZE
        max_nb_of_block_length = self.int_to_bytes(max_transfer_size)
        positive_response_offset = 0x40
        length_format_identifier = len(max_nb_of_block_length) << 4
        request_download_positive_response = [
            IsoServices.RequestDownload + positive_response_offset,
            length_format_identifier,
            *list(max_nb_of_block_length),
        ]
        return request_download_positive_response

    def handle_data_download(
        self, download_request: List[int], aux: UdsServerAuxiliary
    ) -> None:
        """Handle a download request from the client.

        This method handles the entire download functional unit composed of:

        - sending the appropriate RequestDownload response to the received request
        - waiting for the initial TransferData request and sending the ISO TP flow control frame
        - receiving the data blocks until the transfer is finished.

        :param download_request: DownloadData request received from the client.
        """
        self.transfer_successful = False
        # send RequestDownload response
        request_download_response = self.make_request_download_response()
        aux.send_response(request_download_response)
        log.info(
            f"Sent response to request {aux.format_data(download_request)}: {aux.format_data(request_download_response)}"
        )

        # handle data transfer
        block_number = 0
        transfer_size = 0

        # get transfer data size from DownloadData request
        expected_total_transfer_size = self.get_download_data_transfer_size(
            download_request
        )

        while (
            not aux.stop_event.is_set() and transfer_size < expected_total_transfer_size
        ):
            # wait for initial transfer data request
            transfer_request = aux.receive()
            if transfer_request is None:
                continue

            block_number += 1
            log.info(f"Receiving data block number {block_number}")

            # decode PCI to extract the block data length
            (
                first_frame_data_len,
                uds_request_start_index,
            ) = self.get_first_frame_data_length(transfer_request)
            uds_transfer_request = transfer_request[uds_request_start_index:]

            if not uds_transfer_request[0] == aux.services.TransferData:
                log.error(
                    f"Expected TransferData request from ECU, got: {bytes(transfer_request).hex()}"
                )
                return

            # send flow control
            aux.send_flow_control(stmin=self.stmin)

            cnt = 0
            transfer_data_pci_sequence = itertools.cycle(
                tuple(range(0x21, 0x30)) + (0x20,)
            )
            sequence_number = uds_transfer_request[1]
            block_data_len = len(uds_transfer_request) - 2  # remove UDS service bytes

            # receive block data
            while (
                not aux.stop_event.is_set()
                and block_data_len < (first_frame_data_len - 1)
                and cnt < 10
            ):
                data = aux.receive()
                if data is None:
                    cnt += 1
                    time.sleep(1e-4)
                    continue
                cnt = 0
                expected_pci = next(transfer_data_pci_sequence)
                if data[0] != expected_pci:
                    log.warning(
                        f"Consecutive frame missed: expected sequence {hex(expected_pci)}, got {hex(data[0])}"
                    )
                block_data_len += len(data) - 1

            transfer_size += block_data_len
            log.info(f"Got {transfer_size}B out of {expected_total_transfer_size}B")

            success_response = [
                IsoServices.TransferData + aux.POSITIVE_RESPONSE_OFFSET,
                sequence_number,
            ]
            aux.send_response(success_response)

        self.transfer_successful = transfer_size >= expected_total_transfer_size


# request_download_callback = UdsCallback(
#    request=IsoServices.RequestDownload, callback=handle_data_download
# )
