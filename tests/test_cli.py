##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import os

import pytest
from click.testing import CliRunner

from pykiso import cli


@pytest.fixture()
def runner():
    return CliRunner()


def test_main(runner):
    runner.invoke(
        cli.main,
        [
            "pykiso",
            "-c",
            "examples/acroname.yaml",
            "-c",
            "examples/acroname.yaml",
        ],
    )
