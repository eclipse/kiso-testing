##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Fake Flasher Channel for testing
********************************

:module: cc_flasher_example

:synopsis: fake flasher implementation

.. warning: ONLY FOR TESTING PURPOSE!
"""

import logging

from pykiso import Flasher

log = logging.getLogger(__name__)


class FlasherExample(Flasher):
    """A Flasher adapter for testing."""

    def __init__(self, name: str, **kwargs) -> None:
        """Constructor.

        :param name: flasher's alias
        :param kwargs: named arguments
        """
        self.name = name

    def open(self) -> None:
        """Initialize the flasher."""
        log.info("Initialize flasher")
        log.info("Flasher ready!")

    def close(self) -> None:
        """Close flasher and free resources."""
        log.info("Close flasher")
        log.info("Free ressoucres!")

    def flash(self) -> None:
        """Fake a firmware update."""
        log.info("flashing device")
        log.info("flashing device successful")
