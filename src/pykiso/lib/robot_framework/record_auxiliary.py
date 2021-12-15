##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
record auxiliary plugin
***********************

:module: record_auxiliary

:synopsis: implementation of existing RecordAuxiliary for
    Robot framework usage.

.. currentmodule:: record_auxiliary

"""


from robot.api.deco import library

from ..auxiliaries.record_auxiliary import RecordAuxiliary as RecAux
from .aux_interface import RobotAuxInterface


@library(version="0.1.0")
class RecordAuxiliary(RobotAuxInterface):
    """Robot framework plugin for RecordAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=RecAux)
