##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
JLink Flasher
*************

:module: flash_jlink

:synopsis: a Flasher adapter of the pylink-square library

.. currentmodule:: flash_jlink


"""

import logging
import pathlib
import typing

import pylink

from pykiso import Flasher

PathType = typing.Union[str, pathlib.Path]

log = logging.getLogger(__name__)


class JLinkFlasher(Flasher):
    """A Flasher adapter of the pylink-square library."""

    def __init__(
        self,
        binary: PathType = None,
        lib: PathType = None,
        serial_number: int = None,
        chip_name: str = "STM32L562QE",
        speed: int = 9600,
        verbose: bool = False,
        power_on: bool = False,
        start_addr: int = 0,
        xml_path: str = None,
        **kwargs,
    ):
        """Constructor.

        :param binary: path to the binary firmware file
        :param lib: path to the location of the JLink.so/JLink.DLL,
            usually automatically determined
        :param serial_number: optional debugger's S/N (required if
            many connected) (see pylink-square documentation)
        :param chip_name: see pylink-square documentation
        :param speed: see pylink-square documentation
        :param verbose: see pylink-square documentation
        :param power_on: see pylink-square documentation
        :param start_addr: see pylink-square documentation
        :param xml_path: device configuration (see pylink-square
            documentation)
        """
        self.lib = lib
        self.serial_number = serial_number if isinstance(serial_number, int) else None
        self.chip_name = chip_name
        self.speed = speed
        self.verbose = verbose
        self.power_on = power_on
        self.start_addr = start_addr
        self.start_addr = start_addr
        self.xml_path = xml_path
        self.jlink = None
        super().__init__(binary=binary, **kwargs)

    def open(self) -> None:
        """Initialize the flasher."""
        lib = self.lib
        if lib is not None:
            lib = pathlib.Path(self.lib).resolve()
            if lib.exists():
                lib = pylink.Library(dllpath=lib)
            else:
                log.internal_warning(
                    f"No library file found at {lib}, using system default"
                )
                lib = None

        # Define SEGGER J-Link interface
        self.jlink = pylink.JLink(lib=lib)

        # Open a connection to your J-Link
        self.jlink.open(serial_no=self.serial_number)

        # Define the the JLinkInterface
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.JTAG)

        # Set Device config if file provided
        if self.xml_path is not None:
            self.jlink.exec_command(f"JLinkDevicesXMLPath {self.xml_path}")

        # Connect to the target
        self.jlink.connect(self.chip_name, self.speed, self.verbose)

        self.jlink.halt()
        self.jlink.reset()

        log.internal_debug("JLink connected to device")

    def close(self) -> None:
        """Close flasher and free resources."""
        self.jlink.close()

    def flash(self) -> None:
        """¨Perform firmware delivery.

        :raises pylink.JLinkException: if any hardware related error occurred
            during flashing.
        """
        log.internal_debug("flashing device")
        self.jlink.flash_file(
            str(self.binary), addr=self.start_addr, power_on=self.power_on
        )
        self.jlink.reset()
        log.internal_debug("flashing device successful")
