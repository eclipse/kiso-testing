##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

""" This example shows how to use pykiso framework with pytest.
The conftest.py has been created with the tool pykiso_to_pytest.
From the root folder:
pykiso_to_pytest.py examples/dummy.yaml -d examples/pytest/dummy/conftest.py

Run it via:
pytest examples/pytest/dummy/ --log-cli-level=DEBUG

"""


import logging

import pytest


def test_dummy_run(aux2, aux3):
    """This example shows how to access the auxiliaries."""
    logging.info(f"------------suspend auxiliaries run-------------")
    aux3.suspend()
    aux2.suspend()
    logging.info(f"------------resume auxiliaries run--------------")
    aux3.resume()
    aux2.resume()
