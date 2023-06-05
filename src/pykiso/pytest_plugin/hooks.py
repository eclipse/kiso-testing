##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Pykiso-specific hooks for pytest
********************************

:module: hooks

:synopsis: define hooks for test auxiliary fixture customization.

"""

from __future__ import annotations

import pytest

from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface


@pytest.hookspec(firstresult=True)
def pytest_auxiliary_load(aux: str) -> DTAuxiliaryInterface | None:
    """:meta private:"""


@pytest.hookspec(firstresult=True)
def pytest_auxiliary_start(aux: DTAuxiliaryInterface) -> bool | None:
    """Called to start an auxiliary.

    Stops at first non-None result.
    The return value is not used, but only stops further processing.

    :param aux: auxiliary instance that should be started.
    """


@pytest.hookspec(firstresult=True)
def pytest_auxiliary_stop(aux: DTAuxiliaryInterface) -> bool | None:
    """Called to stop an auxiliary.

    Stops at first non-None result.
    The return value is not used, but only stops further processing.

    :param aux: auxiliary instance that should be stopped.
    """
