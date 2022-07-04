##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
uds_auxiliary
*************

:module: uds_auxiliary

:synopsis: Auxiliary used to handle Unified Diagnostic Service protocol

.. currentmodule:: uds_auxiliary

"""
import logging
import threading
import time
from functools import partial
from pathlib import Path
from typing import List, Optional, Union

import can
from uds import IsoServices

from pykiso.connector import CChannel

from .common import uds_exceptions
from .common.uds_base_auxiliary import UdsBaseAuxiliary
from .common.uds_request import UDSCommands
from .common.uds_response import UdsResponse
from .common.uds_utils import get_uds_service

log = logging.getLogger(__name__)


class UdsAuxiliary(UdsBaseAuxiliary):
    """Auxiliary used to handle the UDS protocol on client (tester) side."""

    errors = uds_exceptions

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
        self.tester_present_sender = partial(TesterPresentSender, self)
        super().__init__(
            com,
            config_ini_path,
            odx_file_path,
            request_id,
            response_id,
            **kwargs,
        )

    def transmit(self, data: bytes, req_id: int, extended: bool = False) -> None:
        """Transmit a message through ITF connector. This method is a
        substitute to transmit method present in python-uds package.

        :param data: data to send
        :param req_id: CAN message identifier
        :param extended: True if addressing mode is extended otherwise
            False
        """
        self.channel._cc_send(msg=data, remote_id=req_id, raw=True)

    def send_uds_raw(
        self,
        msg_to_send: Union[bytes, List[int], tuple],
        timeout_in_s: float = 6,
    ) -> Union[UdsResponse, bool]:
        """Send a UDS diagnostic request to the target ECU and check response.

        :param msg_to_send: can uds raw bytes to be sent
        :param timeout_in_s: not used

        :raise ResponseNotReceivedError: raised when no answer has been received
        :raise Exception: raised when the raw message could not be send properly

        :return: the raw uds response's bytes, or True if a response is
            not expected and the command is properly sent otherwise
            False
        """
        try:
            log.info(
                f"UDS request to send '{['0x{:02X}'.format(i) for i in msg_to_send]}'"
            )
            resp = self.uds_config.send(msg_to_send)
        except Exception:
            log.exception("Error while sending uds raw request")
            return False

        if resp is None:
            raise self.errors.ResponseNotReceivedError(msg_to_send)

        resp_print = (
            f"UDS response received {['0x{:02X}'.format(i) for i in resp]}"
            if not isinstance(resp, bool)
            else resp
        )
        log.info(resp_print)
        resp = UdsResponse(resp)
        return resp

    def check_raw_response_positive(self, resp: UdsResponse) -> Optional[bool]:
        """Check if the response is positive, raise an error if not

        :param resp: raw response of uds request

        :raise UnexpectedResponseError: raised when the answer is not the expected one

        :return: True if response is positive
        """
        if resp.is_negative:
            log.info(f"Negative response with NRC: {resp.nrc.name}")
            raise self.errors.UnexpectedResponseError(resp)
        return True

    def check_raw_response_negative(self, resp: UdsResponse) -> Optional[bool]:
        """Check if the response is negative, raise an error if not

        :param resp: raw response of uds request

        :raise UnexpectedResponseError: raised when the answer is not the expected one

        :return: True if response is negative
        """
        if not resp.is_negative:
            raise self.errors.UnexpectedResponseError(resp)
        log.info(f"Negative response with :{resp.nrc.name}")
        return True

    def send_uds_config(
        self, msg_to_send: dict, timeout_in_s: float = 6
    ) -> Union[dict, bool]:
        """Send UDS config to the target ECU.

        :param msg_to_send: uds config to be sent
        :param timeout_in_s: not used

        :return: a dict containing the uds response, or True if a
            response is not expected and the command is properly sent
            otherwise False
        """
        if not self.uds_config_enable:
            log.error("Uds configured without ODX, sending Uds config impossible!")
            return False

        try:
            uds_service_name = get_uds_service(msg_to_send["service"])
            uds_service = getattr(self.uds_config, uds_service_name)
            req_resp_data = uds_service(**msg_to_send["data"])
            if req_resp_data is None:
                req_resp_data = True
            log.info(f"UDS response received {req_resp_data}")
            return req_resp_data
        except AttributeError:
            # Service not found, raised by getattr()
            log.exception(
                f"Could not send UDS config request: unknown service {uds_service_name}"
            )
            return False
        except Exception:
            # Data send failed
            log.exception("Could not send UDS config request: sending failed")
            return False

    def hard_reset(self) -> Union[dict, UdsResponse]:
        """Allow power reset of the component

        :return: response of the hard reset request
        """
        return self.send_uds_raw(UDSCommands.ECUReset.HARD_RESET)

    def force_ecu_reset(self) -> UdsResponse:
        """Allow power reset of the component

        :return: response of the force ecu reset request
        """
        if not self.uds_config_enable:
            return self.send_uds_raw(UDSCommands.ECUReset.KEY_OFF_ON_RESET)
        else:
            ecu_hard_reset_req = {
                "service": IsoServices.EcuReset,
                "data": {"parameter": "ForceEcuReset"},
            }
            return self.send_uds_config(ecu_hard_reset_req)

    def soft_reset(self) -> Union[dict, UdsResponse]:
        """Perform soft reset of the component, equivalent to a restart of application

        :return: response of the soft reset request
        """
        if not self.uds_config_enable:
            return self.send_uds_raw(UDSCommands.ECUReset.SOFT_RESET)
        else:
            ecu_soft_reset_req = {
                "service": IsoServices.EcuReset,
                "data": {"parameter": "Soft Reset"},
            }
            return self.send_uds_config(ecu_soft_reset_req)

    def read_data(self, parameter: str) -> Optional[Union[dict, bool]]:
        """UDS config command that allow data reading

        :param parameter: data to be read

        :return: a dict with uds config response
        """
        if self.uds_config_enable:
            req = {
                "service": IsoServices.ReadDataByIdentifier,
                "data": {
                    "parameter": parameter,
                },
            }
            return self.send_uds_config(req)
        else:
            log.error("No uds config found")
            return

    def write_data(
        self, parameter: str, value: Union[List[bytes], bytes]
    ) -> Optional[Union[dict, bool]]:
        """UDS config command that allow data writing

        :param parameter: data to be set
        :param value: new content of the data

        :return: a dict with uds config response
        """
        if self.uds_config_enable:
            req = {
                "service": IsoServices.WriteDataByIdentifier,
                "data": {"parameter": parameter, "dataRecord": value},
            }
            return self.send_uds_config(req)
        else:
            log.error("No uds config found")
            return

    def _receive_message(self, timeout_in_s: float) -> None:
        """This method is only used to populate the python-uds reception
        buffer. When a message is received, invoke python-uds configured
        callback to make it available for pyton-uds

        :param timeout_in_s: timeout on reception.
        """

        recv_response = self.channel.cc_receive(timeout=timeout_in_s, raw=True)
        received_data = recv_response.get("msg")
        arbitration_id = recv_response.get("remote_id")

        if received_data is not None:
            can_msg = can.Message(
                data=received_data, arbitration_id=arbitration_id, is_extended_id=False
            )
            if arbitration_id == self.res_id:
                self.uds_config.tp.callback_onReceive(can_msg)

    def _abort_command(self) -> None:
        """Not used."""
        pass

    def _run_command(self, cmd_message, cmd_data=None) -> Union[dict, bytes, bool]:
        """Not used."""
        pass

    def _get_instance(self):
        return self


class TesterPresentSender(threading.Thread):
    """Self that continuously sends tester present messages via UDS"""

    TESTER_PRESENT_SEND = b"\x3E\x00"

    def __init__(self, uds_aux: UdsAuxiliary, period: float = 4):
        """Constructor

        :param period: period to use for the cyclic sending of tester present
        :param uds_aux: auxiliary used to send tester present
        """
        self.uds_aux = uds_aux
        self.period = period
        self.stop_event = threading.Event()
        super().__init__(name="TesterPresentSender")

    def run(self):
        """send tester present at defined period until stopped"""
        while not self.stop_event.is_set():
            self.uds_aux.transmit(self.TESTER_PRESENT_SEND, self.uds_aux.req_id)
            time.sleep(self.period)

    def __enter__(self):
        """Start the thread."""
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        """Stop the thread."""
        self.stop_event.set()
