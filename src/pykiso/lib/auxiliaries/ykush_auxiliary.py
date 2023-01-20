##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Ykush Auxiliary
***************

:module: ykush_auxiliary

:synopsis: Auxiliary that can power on and off ports on an Ykush device.

.. currentmodule:: ykush_auxiliary

"""
import logging
from contextlib import contextmanager
from enum import IntEnum
from typing import Any, List, Optional, Tuple

import hid

from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface

log = logging.getLogger(__name__)

# YKUSH device USB VID
YKUSH_USB_VID = 0x04D8
# YKUSH PIDs when in normal operation mode: YKUSH beta, YKUSH, YKUSH3, YKUSHXS
YKUSH_USB_PID_LIST = (0x0042, 0xF2F7, 0xF11B, 0xF0CD)

# YKUSH device USB comm declarations
YKUSH_USB_TIMEOUT = 1000  # timeout in ms
YKUSH_USB_PACKET_SIZE = 64
YKUSH_USB_PACKET_PAYLOAD_SIZE = 20

# YKUSH device protocol status declarations
YKUSH_PROTO_OK_STATUS = 1

# YKUSH port state meaning declarations
YKUSH_PORT_STATE_ON = 1
YKUSH_PORT_STATE_OFF = 0
YKUSH_PORT_STATE_ERROR = 255
YKUSH_PORT_STATE_DICT = {0: "OFF", 1: "ON", 255: "ERROR"}


class YkushError(Exception):
    """General Ykush specific exception used as basis for all others."""

    pass


class YkushDeviceNotFound(YkushError):
    """Raised when no Ykush device is found."""

    pass


class YkushStatePortNotRetrieved(YkushError):
    """Raised when the state of a port can't be retrieved."""

    pass


class YkushSetStateError(YkushError):
    """Raised when a port couldn't be switched on or off."""

    pass


class YkushPortNumberError(YkushError):
    """Raised when the port number doesn't exist."""

    pass


class PortState(IntEnum):
    OFF = 0
    ON = 1


class YkushAuxiliary(DTAuxiliaryInterface):
    """Auxiliary used to power on and off the ports."""

    def __init__(self, serial_number: str = None, **kwargs):
        """Initialize attribute

        :param serial: Serial number of the device to connect, if he is not defined
            then it will connect to the first Ykush device it find, defaults to None.
        :raises YkushDeviceNotFound: If no device is found or the serial number
            is not the serial of one device.
        """
        super().__init__(
            is_proxy_capable=False,
            tx_task_on=False,
            rx_task_on=False,
            connector_required=False,
            **kwargs,
        )
        self._ykush_device = None
        self._product_id = None
        self._path = None
        self.connect_device(serial_number)
        self.number_of_port = self.get_number_of_port()

    def _create_auxiliary_instance(self) -> bool:
        """Power on all port at the start.
        :return: True if succesful
        """
        log.internal_info("Create auxiliary instance")
        self.set_all_ports_on()
        return True

    def _delete_auxiliary_instance(self) -> bool:
        """Power on all port to restore the ports.
        :return: always True
        """
        self.set_all_ports_on()
        log.internal_info("Auxiliary instance deleted")
        return True

    def connect_device(self, serial: int = None):
        """Find an Ykush device, will automatically connect to the first one
        it find, if you have multiple connected you have to precise the serial
        number of the device.

        :param serial: serial number of the device, defaults to None
        :raises YkushDeviceNotFound: if no ykush device is found
        """
        list_ykush_device = []
        self._path = None
        # try to locate a device
        for device in hid.enumerate(0, 0):
            if (
                device["vendor_id"] == YKUSH_USB_VID
                and device["product_id"] in YKUSH_USB_PID_LIST
            ):
                list_ykush_device.append(device["serial_number"])
                if serial is None or serial == device["serial_number"]:
                    self._product_id = device["product_id"]
                    self._path = device["path"]

        if self._path is not None:
            self._ykush_device = hid.device()
            self._ykush_device.open_path(self._path)
        else:
            if list_ykush_device == []:
                raise YkushDeviceNotFound(
                    "Could not connect to a ykush hub, no device was found."
                )
            else:
                raise YkushDeviceNotFound(
                    f"The serial numbers available are : {list_ykush_device}\n"
                    f"No device was found with the serial number {serial}\n"
                    if serial
                    else "",
                )

    @contextmanager
    def _open_and_close_device(self):
        """Context manager to open and close device every time we send a message
        otherwise  we will get an empty message every time in response.
        """
        self._ykush_device = hid.device()
        self._ykush_device.open_path(self._path)
        try:
            yield
        finally:
            self._ykush_device.close()

    def check_port_number(self, port_number: int):
        """Check if the port indicated is a port of the device

        :raises YkushPortNumberError: Raise error if no port has this number
        """
        if port_number not in range(1, self.number_of_port + 1):
            raise YkushPortNumberError(
                f"The port number {port_number} is not valid for the device,"
                f" it has only {self.number_of_port} ports"
            )

    @staticmethod
    def get_str_state(state: int) -> str:
        """Return the str of a state

        :param state: 1 (port on), 0 (port off)
        :return: ON, OFF
        """
        return YKUSH_PORT_STATE_DICT[state]

    def get_serial_number_string(self) -> str:
        """Returns the device serial number string"""
        with self._open_and_close_device():
            return self._ykush_device.get_serial_number_string()

    def get_number_of_port(self) -> int:
        """Returns the number of port on the ykush device"""
        # original YKUSH 1,3 port count
        count = 3
        # YKUSHXS Make it have 1 port
        if self._product_id == 0xF0CD:
            count = 1

        return count

    def get_port_state(self, port_number: int) -> PortState:
        """Returns a specific port state.

        :raises YkushStatePortNotRetrieved: If the state couldn't be retrieved
        :return: 0 if the port is off, 1 if the port is on
        """
        self.check_port_number(port_number)
        return self.get_all_ports_state()[port_number - 1]

    def get_all_ports_state(self) -> List[PortState]:
        """Returns the state of all the ports.

        :raises YkushStatePortNotRetrieved: The states couldn't be retrieved
        :return: list with 0 if a port is off, 1 if on
        """
        if self.get_firmware_version()[0] >= 1:
            recvbytes = self._raw_sendreceive([0x2A])[: self.number_of_port + 1]
            if recvbytes[0] == YKUSH_PROTO_OK_STATUS:
                return [
                    PortState.ON if p > 0x10 else PortState.OFF for p in recvbytes[1:]
                ]
            else:
                raise YkushStatePortNotRetrieved(
                    "The states of the ports couldn't be retrieved"
                )
        else:
            # firmware glitch workaround
            list_state = []
            for port_number in range(1, self.number_of_port + 1):
                status, port_state = self._raw_sendreceive([0x20 | port_number])[:2]
                if status == YKUSH_PROTO_OK_STATUS:
                    list_state.append(
                        PortState.ON if port_state > 0x10 else PortState.OFF
                    )
                else:
                    raise YkushStatePortNotRetrieved(
                        f"The state of the port {port_number} couldn't be retrieved"
                    )
            return list_state

    def get_firmware_version(self) -> Tuple[int, int]:
        """Returns a tuple with YKUSH firmware version in format (major, minor)."""

        status, major, minor = self._raw_sendreceive([0xF0])[:3]
        if status == YKUSH_PROTO_OK_STATUS:
            self._firmware_major_version, self._firmware_minor_version = (
                major,
                minor,
            )
        else:
            # early devices will not recognize it, figure it out from serial
            self._firmware_major_version = 1
            self._firmware_minor_version = (
                2
                if "YK2" in self.get_serial_number_string()
                else 255
                if "YKD2" in self.get_serial_number_string()
                else 0
            )
        return self._firmware_major_version, self._firmware_minor_version

    def set_port_state(self, port_number: int, state: int):
        """Set a specific port On or Off.

        :raises YkushSetStateError: if the operation had an error
        :param state: 1 (port on), 0 (port off)
        """
        str_state = self.get_str_state(state)
        self.check_port_number(port_number)
        self._raw_sendreceive(
            [(0x10 if state == YKUSH_PORT_STATE_ON else 0x0) | port_number]
        )

        try:
            state_port = self.get_port_state(port_number)
        except YkushStatePortNotRetrieved as e:
            raise YkushSetStateError(
                f"The state of the action to power {str_state}"
                "couldn't be confirmed because the state of the port can't be retrieved"
            ) from e
        if state_port != PortState[str_state]:
            raise YkushSetStateError(
                f"There was an error trying to power {str_state.lower()} the port,"
                f"the port {port_number} is {state_port}"
            )

    def set_port_on(self, port_number: int):
        """Power on a specific port.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_port_state(port_number, state=YKUSH_PORT_STATE_ON)

    def set_port_off(self, port_number: int):
        """Power off a specific port.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_port_state(port_number, state=YKUSH_PORT_STATE_OFF)

    def set_all_ports(self, state: int):
        """Power off or on all YKUSH ports.

        :param state: state wanted 1 for On, 0 for Off
        :raises YkushSetStateError: if the operation had an error
        """
        str_state = self.get_str_state(state)
        self._raw_sendreceive([(0x1A if state == YKUSH_PORT_STATE_ON else 0x0A)])

        try:
            states_port = self.get_all_ports_state()
        except YkushStatePortNotRetrieved as e:
            raise YkushSetStateError(
                f"The state of the action to power {str_state}"
                "couldn't be confirmed because the state of the ports can't be retrieved"
            ) from e

        if not (PortState[str_state] == states_port[0] and len(set(states_port)) == 1):
            raise YkushSetStateError(
                "There was an error during the power "
                f"{str_state.lower()},"
                f"the ports have the following states : {states_port}"
            )

    def set_all_ports_on(self):
        """Power on all YKUSH downstreams ports.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_all_ports(state=YKUSH_PORT_STATE_ON)

    def set_all_ports_off(self):
        """Power off all YKUSH downstreams ports.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_all_ports(state=YKUSH_PORT_STATE_OFF)

    def is_port_on(self, port_number: int) -> bool:
        """Check if a port is on.

        :return: True if a port is on, else False
        """
        return bool(self.get_port_state(port_number))

    def is_port_off(self, port_number: int) -> bool:
        """Check if a port is off.

        :return: True if a port is off, else False
        """
        return not bool(self.get_port_state(port_number))

    def _raw_sendreceive(self, packetarray) -> List[int]:
        """Send a message to the device and get the returned message.

        :param packetarray: packet to send to do an operation
        :return: response to the message send
        """
        with self._open_and_close_device():
            packetarray = packetarray * 2 + [0x00] * (
                YKUSH_USB_PACKET_SIZE - len(packetarray)
            )
            self._ykush_device.write(packetarray)
            recvpacket = self._ykush_device.read(
                max_length=YKUSH_USB_PACKET_SIZE + 1, timeout_ms=YKUSH_USB_TIMEOUT
            )

            # if not None return the bytes we actually need
            if recvpacket is None or len(recvpacket) < YKUSH_USB_PACKET_PAYLOAD_SIZE:
                return [0xFF] * YKUSH_USB_PACKET_PAYLOAD_SIZE
            return recvpacket[:YKUSH_USB_PACKET_PAYLOAD_SIZE]

    def _run_command(self, cmd_message: Any, cmd_data: Optional[bytes]) -> None:
        """Not used.

        Simply respect the interface.
        """

    def _receive_message(self, timeout_in_s: float) -> None:
        """Not used.

        Simply respect the interface.
        """
