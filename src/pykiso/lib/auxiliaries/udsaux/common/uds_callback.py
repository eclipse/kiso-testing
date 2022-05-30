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
    along with callbacks for functional requests (TransferData services).

.. currentmodule:: uds_callback

"""
from __future__ import annotations

import itertools
import logging
import time
import typing
from dataclasses import dataclass
from typing import Callable, List, Optional, Union

from uds import IsoServices

if typing.TYPE_CHECKING:
    from pykiso.lib.auxiliaries.udsaux import UdsServerAuxiliary


log = logging.getLogger(__name__)


@dataclass
class UdsCallback:
    """Class used to store information needed for UDS callbacks.

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
            self.callback(aux, received_request)
        else:
            aux.send_response(self.response)

    @staticmethod
    def int_to_bytes(integer: int) -> bytes:
        return integer.to_bytes((integer.bit_length() + 7) // 8, "big")


def handle_data_download(
    aux: UdsServerAuxiliary, download_data_request: List[int]
) -> None:
    """Handle a download request from the client.

    This method handles the entire download functional unit composed of:

    - sending the appropriate RequestDownload response to the received request
    - waiting for the initial TransferData request and sending the ISO TP flow control frame
    - receiving the data blocks until the transfer is finished.

    :param download_data_request: DownloadData request received from the client.
    """
    # send RequestDownload response
    max_nb_of_block_length = UdsCallback.int_to_bytes(aux.MAX_TRANSFER_SIZE)
    length_format_identifier = len(max_nb_of_block_length) << 4
    response = [
        aux.services.RequestDownload + aux.POSITIVE_RESPONSE_OFFSET,
        length_format_identifier,
        *list(max_nb_of_block_length),
    ]
    aux.send_response(response)
    log.info(
        f"Sent response to request {aux.format_data(download_data_request)}: {aux.format_data(response)}"
    )

    # handle data transfer
    block_number = 0
    transfer_size = 0

    address_and_length_format_identifier = download_data_request[1]
    nb_bytes_size_param = address_and_length_format_identifier & 0xF0
    expected_total_transfer_size = int.from_bytes(
        bytes(download_data_request[-nb_bytes_size_param:]), byteorder="big"
    )

    while not aux.stop_event.is_set() and transfer_size < expected_total_transfer_size:
        # wait for initial transfer data request
        data_transfer_request = aux.receive()
        if data_transfer_request is None:
            continue

        block_number += 1
        log.info(f"Receiving data block number {block_number}")

        # decode PCI to extract the block data length
        first_frame_data_len = (
            data_transfer_request[0] & 0x0F
        ) + data_transfer_request[1]
        if first_frame_data_len == 0:
            first_frame_data_len = int.from_bytes(
                bytes(data_transfer_request[2:6]), byteorder="big"
            )
            data_transfer_request = data_transfer_request[6:]
        else:
            data_transfer_request = data_transfer_request[2:]

        if not data_transfer_request[0] == aux.services.TransferData:
            log.error(
                f"Expected TransferData request from ECU, got: {bytes(data_transfer_request).hex()}"
            )
            return

        # send flow control
        aux.send_flow_control(stmin=0.1)

        cnt = 0
        sequence_number = data_transfer_request[1]
        received_data = bytes(data_transfer_request)
        data_len = len(received_data) - 2  # remove UDS service bytes

        transfer_data_pci_sequence = itertools.cycle(tuple(range(0x21, 0x30)) + (0x20,))

        # receive block data
        while (
            not aux.stop_event.is_set()
            and data_len < first_frame_data_len
            and cnt < 1000
        ):
            data = aux.receive()
            if not data:
                cnt += 1
                time.sleep(1e-6)
                continue
            cnt = 0
            expected_pci = next(transfer_data_pci_sequence)
            if data[0] != expected_pci:
                log.warning(
                    f"Missed packet reception: "
                    f"expected sequence {hex(expected_pci)}, got {hex(data[0])}"
                )
            data_len += len(data) - 1

        transfer_size += data_len
        log.info(f"Got {transfer_size}B out of {expected_total_transfer_size}B")

        # respond with sequence number
        log.info(
            f"Sequence number: {sequence_number} || Total received data length: {data_len}"
        )
        success_response = [
            aux.services.TransferData + aux.POSITIVE_RESPONSE_OFFSET,
            sequence_number,
        ]
        log.info(f"Sent TranferData response: {bytes(success_response).hex()}")
        aux.send_response(success_response)


request_download_callback = UdsCallback(
    request=IsoServices.RequestDownload, callback=handle_data_download
)
