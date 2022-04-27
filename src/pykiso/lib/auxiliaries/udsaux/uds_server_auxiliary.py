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
import configparser
import logging
import threading
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from uds import Uds, createUdsConnection
from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.FunctionCreation.ClearDTCMethodFactory import (
    ClearDTCMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.DiagnosticSessionControlMethodFactory import (
    DiagnosticSessionControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ECUResetMethodFactory import (
    ECUResetMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.InputOutputControlMethodFactory import (
    InputOutputControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ReadDataByIdentifierMethodFactory import (
    ReadDataByIdentifierMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ReadDTCMethodFactory import (
    ReadDTCMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RequestDownloadMethodFactory import (
    RequestDownloadMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RequestUploadMethodFactory import (
    RequestUploadMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RoutineControlMethodFactory import (
    RoutineControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.SecurityAccessMethodFactory import (
    SecurityAccessMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TesterPresentMethodFactory import (
    TesterPresentMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TransferDataMethodFactory import (
    TransferDataMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TransferExitMethodFactory import (
    TransferExitMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.WriteDataByIdentifierMethodFactory import (
    WriteDataByIdentifierMethodFactory,
)
from uds.uds_config_tool.ISOStandard.ISOStandard import IsoServices
from uds.uds_config_tool.UdsConfigTool import get_serviceIdFromXmlElement

from pykiso.connector import CChannel
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface

from . import uds_exceptions
from .uds_utils import get_uds_service

log = logging.getLogger(__name__)


service_to_positive_response_func = {
    IsoServices.ClearDiagnosticInformation: ClearDTCMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.DiagnosticSessionControl: DiagnosticSessionControlMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.EcuReset: ECUResetMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.InputOutputControlByIdentifier: InputOutputControlMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.ReadDataByIdentifier: ReadDataByIdentifierMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.ReadDTCInformation: ReadDTCMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.RequestDownload: RequestDownloadMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.RequestTransferExit: TransferExitMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.RequestUpload: RequestUploadMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.RoutineControl: RoutineControlMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.SecurityAccess: SecurityAccessMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.TesterPresent: TesterPresentMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.TransferData: TransferDataMethodFactory.create_encodePositiveResponseFunction,
    IsoServices.WriteDataByIdentifier: WriteDataByIdentifierMethodFactory.create_encodePositiveResponseFunction,
}


@dataclass
class UdsCallback:
    request: Union[int, bytes]  # e.g. 0x1003 or b'\x10\x03'
    response: Union[int, bytes]  # e.g. 0x50034911 or b'\x50\x03\x49\x11'
    response_length: int = None

    def __post_init__(self):
        if isinstance(self.request, int):
            self.request = UdsCallback.int_to_bytes(self.request)
        if isinstance(self.response, int):
            self.response = UdsCallback.int_to_bytes(self.response)

        if self.response_length is None:
            self.response_length = len(self.response)
        else:
            self.response = self.response.ljust(self.response_length, b"\x00")

    @staticmethod
    def int_to_bytes(integer: int) -> bytes:
        return integer.to_bytes((integer.bit_length() + 7) // 8, "big")


class UdsServerAuxiliary(AuxiliaryInterface):
    """Auxiliary used to handle UDS messages"""

    POSITIVE_RESPONSE_OFFSET = 0x40
    errors = uds_exceptions

    def __init__(
        self,
        com: CChannel,
        config_ini_path: str,
        callbacks: Optional[List[UdsCallback]] = None,
        odx_file_path: str = None,
        **kwargs,
    ):
        """Initialize attributes.

        :param com: communication channel connector.
        :param config_ini_path: uds parameters file.
        :param odx_file_path: ecu diagnostic definition file.
        """
        self.channel = com
        self.odx_file_path = odx_file_path
        if odx_file_path:
            self.odx_file_path = Path(odx_file_path)
            self.sid_to_did_to_name = UdsServerAuxiliary._parse_odx(self.odx_file_path)

        self.config_ini_path = Path(config_ini_path)

        config = configparser.ConfigParser()
        config.read(self.config_ini_path)

        self.req_id = int(config.get("can", "defaultReqId"), 16)
        self.res_id = int(config.get("can", "defaultResId"), 16)

        self.uds_config_enable = False
        self.uds_config = None

        self.callbacks = callbacks or list()

        self._callback_lock = threading.Lock()

        super().__init__(is_proxy_capable=True, **kwargs)

    @staticmethod
    def _parse_odx(odx_file) -> Dict[int, Dict[int, str]]:

        sid_to_human_name = {}
        xml_elements = {}

        root = ET.parse(odx_file)

        for child in root.iter():
            try:
                xml_elements[child.attrib["ID"]] = child
            except KeyError:
                pass

        for value in xml_elements.values():
            if value.tag == "DIAG-SERVICE":
                sid = get_serviceIdFromXmlElement(value, xml_elements)
                sid_to_human_name[sid] = {}
                sdg = value.find("SDGS").find("SDG")
                human_name = ""
                for sd in sdg:
                    try:
                        if sd.attrib["SI"] == "DiagInstanceName":
                            human_name = sd.text
                            # TODO NOT ENOUGH (sd is ET.Element)
                            sid_to_human_name[sid][sd] = human_name
                    except KeyError:
                        pass

        return sid_to_human_name

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
            # use Server TP layer instead of the default client implementation
            # self.uds_config.tp = ServerCanTp(
            #    configPath=self.config_ini_path,
            #    bus=bus,
            #    interface=interface,
            #    reqId=self.req_id,
            #    resId=self.res_id,
            # )
            # replace transmit method from python-uds with a method
            # using ITF's connector
            self.uds_config.tp.overwrite_transmit_method(self.transmit)
            return True
        except Exception:
            log.exception("Error during channel creation")
            self.stop()
            return False

    def transmit(self, data: bytes, req_id: int, extended: bool = False) -> None:
        """Transmit a message through ITF connector. This method is a
        substitute to transmit method present in python-uds package.

        :param data: data to send
        :param req_id: CAN message identifier
        :param extended: True if addressing mode is extended otherwise
            False
        """
        self.channel._cc_send(msg=data, remote_id=req_id, raw=True)

    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        log.info("Delete auxiliary instance")
        self.uds_config.disconnect()
        self.channel.close()
        return True

    def register_callback(
        self, request, response, response_length: Optional[int] = None
    ):
        with self._callback_lock:
            self.callbacks.append(
                UdsCallback(
                    request=request, response=response, response_length=response_length
                )
            )

    def _receive_message(self, timeout_in_s: float) -> None:
        """This method is only used to populate the python-uds reception
        buffer. When a message is received, invoke python-uds configured
        callback to make it available for python-uds

        :param timeout_in_s: timeout on reception.
        """
        received_data, arbitration_id = self.channel.cc_receive(
            timeout=timeout_in_s, raw=True
        )
        if received_data is not None and arbitration_id == self.req_id:
            uds_data = self.uds_config.tp.decode_isotp(
                received_data=received_data, use_external_snd_rcv_functions=True
            )
            with self._callback_lock:
                self._dispatch_callback(uds_data)

    def _dispatch_callback(self, received_uds_data: bytes):
        if self.uds_config_enable:
            # find "human name" for the received data
            sid = received_uds_data[0]
            did_to_name = self.sid_to_did_to_name[sid]
            name = did_to_name.get(received_uds_data[1]) or did_to_name.get(
                received_uds_data[1:3]
            )
            if name is None:
                return
            # run the positive response function registered for the "human name"
            service_name = get_uds_service(sid)
            service = getattr(self.uds_config, service_name + "Container")
            # TODO IT REQUIRES THE "HUMAN NAME"
            response = service.positiveResponseFunctions[name]

            ### ALTERNATIVE
            service_encode_func = service_to_positive_response_func[sid]
        else:
            for callback in self.callbacks:
                if received_uds_data == callback.request:
                    response = callback.response
                    break

        self.uds_config.tp.encode_isotp(response, use_external_snd_rcv_functions=True)

    def _abort_command(self) -> None:
        """Not used."""
        pass

    def _run_command(self, cmd_message, cmd_data=None) -> Union[dict, bytes, bool]:
        """Not used."""
        pass
