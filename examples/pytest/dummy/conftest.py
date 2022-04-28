##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pytest

from pykiso.lib.auxiliaries.dut_auxiliary import DUTAuxiliary
from pykiso.lib.auxiliaries.example_test_auxiliary import ExampleAuxiliary
from pykiso.lib.connectors.cc_example import CCExample


@pytest.fixture(scope="session")
def aux1():
    try:
        com = CCExample(name="chan1")
        aux1 = ExampleAuxiliary(
            com=com,
        )
        aux1.start()
        aux1.create_instance()
    except Exception:
        logging.exception("something bad happened")
    yield aux1
    aux1.delete_instance()
    aux1.stop()


@pytest.fixture(scope="session")
def aux2():
    try:
        com = CCExample(name="chan2")
        flash = CCExample(name="chan2")
        aux2 = ExampleAuxiliary(
            com=com,
            flash=flash,
        )
        aux2.start()
        aux2.create_instance()
    except Exception:
        logging.exception("something bad happened")
    yield aux2
    aux2.delete_instance()
    aux2.stop()


@pytest.fixture(scope="session")
def aux3():
    try:
        com = CCExample(name="chan4")
        aux3 = DUTAuxiliary(
            com=com,
        )
        aux3.start()
        aux3.create_instance()
    except Exception:
        logging.exception("something bad happened")
    yield aux3
    aux3.delete_instance()
    aux3.stop()
