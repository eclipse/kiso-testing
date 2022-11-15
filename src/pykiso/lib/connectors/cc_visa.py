##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel using VISA protocol
*****************************************

:module: cc_visa

:synopsis: VISA communication channel to communicate to instruments using SCPI protocol.

.. currentmodule:: cc_visa

"""

import abc
import logging
from typing import Dict, Optional

import pyvisa

from pykiso import CChannel
from pykiso.types import MsgType

log = logging.getLogger(__name__)


class VISAChannel(CChannel):
    """VISA Interface for devices communicating with SCPI"""

    def __init__(self, **kwargs):
        """Initialize channel settings."""
        # Use PyVISA Resource Manager with PyVISA-py backend
        self.ResourceManager = pyvisa.ResourceManager("@py")
        # Instantiate message-based resource:
        self.resource_name = "messagebased_resource"
        self.resource = pyvisa.resources.messagebased.MessageBasedResource(
            self.ResourceManager, self.resource_name
        )
        super().__init__(**kwargs)

    @abc.abstractmethod
    def _cc_open(self) -> None:
        """Open an instrument"""
        pass

    def _cc_close(self) -> None:
        """Close a resource"""
        log.internal_info(f"Close VISA resource: {self.resource_name}")
        self.resource.close()

    def _process_request(self, request: str, request_data: str = "") -> str:
        """Send a SCPI request.

        :param request: command request to the instrument (write, read or query)
        :param request_data: command payload (for write and query requests only)

        :return: response message from the instrument (read and query requests)
            or an empty string for write requests and if read or query request failed.
        """
        recv = ""
        try:
            if request == "read":
                log.internal_debug(f"Reading {self.resource_name} ")
                recv = self.resource.read().strip()
            elif request == "query":
                log.internal_debug(f"Querying {request_data} to {self.resource_name}")
                recv = self.resource.query(request_data).strip()
            else:
                log.internal_warning(f"Unknown request '{request}'!")

        except pyvisa.errors.InvalidSession:
            log.exception(
                f"Request {request}:{request_data} failed! Invalid session (resource might be closed)."
            )
        except pyvisa.errors.VisaIOError:
            log.exception(
                f"Request {request}:{request_data} failed! Timeout expired before operation completed."
            )
        except Exception as e:
            log.exception(f"Request {request}: {request_data} failed!\n{e}")
        else:
            log.internal_debug(f"Response received: {recv}")
        finally:
            response = {"msg": str(recv)}
            return response

    def _cc_send(self, msg: MsgType) -> None:
        """Send a write request to the instrument

        :param msg: message to send
        """
        msg = msg.decode()

        log.internal_debug(f"Writing {msg} to {self.resource_name}")
        self.resource.write(msg)

    def _cc_receive(self, timeout: float = 0.1) -> Dict[str, Optional[bytes]]:
        """Send a read request to the instrument

        :param timeout: time in second to wait for reading a message


        :return: the received response message, or an empty string if the request
            expired with a timeout.
        """

        return {"msg": self._process_request("read")["msg"].encode()}

    def query(self, query_command: str) -> str:
        """Send a query request to the instrument

        :param query_command: query command to send

        :return: Response message, None if the request expired with a timeout.
        """
        return self._process_request("query", query_command)


class VISASerial(VISAChannel):
    """Connector used to communicate with an instrument via Serial."""

    def __init__(self, serial_port: int, baud_rate=9600, **kwargs):
        """Initialize channel attributes.

        :param serial_port: COM port to use to connect to the instrument
        :param baud_rate: baud rate used to communicate with the instrument
        """
        # Use PyVISA Resource Manager with PyVISA-py backend
        super().__init__(**kwargs)
        # Redefining resource name and type for serial communication
        self.resource_name = f"ASRL{serial_port}::INSTR"
        self.baud_rate = baud_rate
        self.resource = pyvisa.resources.serial.SerialInstrument(
            self.ResourceManager, self.resource_name
        )

    def _cc_open(self) -> None:
        """Open an instrument via serial"""
        log.internal_info(f"Open VISA resource: {self.resource_name}")
        # check if the resource is available (for Serial only)
        if self.resource_name not in self.ResourceManager.list_resources():
            raise ConnectionRefusedError(
                f"The resource named {self.resource_name} is unavailable and cannot be opened."
            )
        elif self.resource_name in [
            res.resource_name for res in self.ResourceManager.list_opened_resources()
        ]:
            raise ConnectionRefusedError(
                f"The resource named {self.resource_name} is opened and cannot be opened again."
            )
        else:
            self.resource = self.ResourceManager.open_resource(
                self.resource_name, baud_rate=self.baud_rate
            )


class VISATcpip(VISAChannel):
    """Connector used to communicate with an instrument via TCPIP"""

    def __init__(self, ip_address: str, protocol="INSTR", **kwargs):
        """Initialize channel attributes.

        :param ip_address: target instrument's ip address
        :param protocol: communication protocol to use
        """
        # Use PyVISA Resource Manager with PyVISA-py backend
        super().__init__(**kwargs)
        # Redefining resource name and type for TCPIP communication
        self.ip_address = ip_address
        self.resource_name = f"TCPIP::{ip_address}::{protocol}"
        self.resource = pyvisa.resources.tcpip.TCPIPInstrument(
            self.ResourceManager, self.resource_name
        )
        self.protocol = protocol

    def _cc_open(self) -> None:
        """Open a remote instrument via TCPIP"""
        log.internal_info(f"Open VISA resource: {self.resource_name}")
        self.resource = self.ResourceManager.open_resource(self.resource_name)
