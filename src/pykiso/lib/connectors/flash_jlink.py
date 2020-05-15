"""
JLink Flasher
*************

:module: flash_jlink

:synopsis: a Flasher adapter of the pylink-square library

.. currentmodule:: flash_jlink

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

"""

import typing
import pylink
import pathlib
import logging

from pykiso import Flasher

PathType = typing.Union[str, pathlib.Path]


class JLinkFlasher(Flasher):
    """ a Flasher adapter of the pylink-square library """

    def __init__(
        self,
        binary: PathType = None,
        lib: PathType = None,
        chip_name: str = "STM32L562QE",
        speed: int = 9600,
        verbose: bool = False,
        power_on: bool = False,
        start_addr: int = 0,
        **kwargs,
    ):
        """constructor

        :param binary: path to the binary firmware file
        :param lib: path to the location of the JLink.so/JLink.DLL, usually automatically
            determined
        :param chip_name: see pylink-square documentation
        :param speed: see pylink-square documentation
        :param verbose: see pylink-square documentation
        :param power_on: see pylink-square documentation
        :param start_addr: see pylink-square documentation
        """
        self.lib = lib
        self.chip_name = chip_name
        self.speed = speed
        self.verbose = verbose
        self.power_on = power_on
        self.start_addr = start_addr
        self.power_on = power_on
        self.start_addr = start_addr
        super(JLinkFlasher, self).__init__(binary=binary, **kwargs)

    def open(self):
        """ initialize the flasher """
        lib = self.lib
        if lib is not None:
            lib = pathlib(self.lib).resolve()
            if lib.exists():
                lib = pylink.Library(lib=lib)
            else:
                logging.warn(f"No library file found at {lib}, using system default")
                lib = None
        self.jlink = pylink.JLink(lib=lib)
        self.jlink.connect(self.chip_name, self.speed, self.verbose)
        logging.debug(f"JLink connected to device")

    def close(self):
        """close flasher and free ressources"""
        self.jlink._finalize()

    def flash(self):
        """ perform firmware delivery """
        logging.debug(f"flashing device")
        try:
            self.jlink.flash_file(
                self.binary, start_addr=self.start_addr, power_on=self.power_on
            )
        except pylink.JLinkException as e:
            logging.exception("flashing of device has failed", exc_info=True)
        else:
            logging.debug(f"flashing device successful")
