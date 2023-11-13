##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import importlib
import sys
from pathlib import Path

import pytest

from pykiso.lib.connectors import flash_jlink
from pykiso.lib.connectors.flash_jlink import JLinkFlasher, pylink


@pytest.fixture
def mock_jlink(mocker):
    """
    replace pylink.JLink and pylink.Library with mocks
    """

    class MockJLink:
        def __init__(self, lib, **kwargs):
            pass

        connect = mocker.stub(name="connect")
        set_tif = mocker.stub(name="set_tif")
        open = mocker.stub(name="open")
        close = mocker.stub(name="close")
        exec_command = mocker.stub(name="exec_command")
        halt = mocker.stub(name="halt")
        reset = mocker.stub(name="reset")
        flash_file = mocker.stub(name="flash_file")
        erase = mocker.stub(name="erase")

    class MockJLib:
        def __init__(self, lib=None, **kwargs):
            pass

    mocker.patch.object(pylink, "JLink", new=MockJLink)
    mocker.patch.object(pylink, "Library", new=MockJLib)
    return pylink


def test_import():
    with pytest.raises(ImportError):
        sys.modules["pylink"] = None
        importlib.reload(flash_jlink)
    sys.modules["pylink"] = pylink
    importlib.reload(flash_jlink)


@pytest.mark.parametrize(
    "return_value",
    [True, False],
)
def test_open(mocker, tmp_file, mock_jlink, return_value):
    Jlink_inst = JLinkFlasher(tmp_file)
    Jlink_inst.lib = Path()
    Jlink_inst.xml_path = "test_xml"
    mock_exist = mocker.patch.object(Path, "exists", return_value=return_value)
    Jlink_inst.open()
    mock_exist.assert_called()


def test_jlink_flasher(tmp_file, mock_jlink):
    """assert that the correct library functions are called"""
    with JLinkFlasher(tmp_file, serial_number=1234) as fl:
        fl.flash()

    mock_jlink.JLink.connect.assert_called_once()
    mock_jlink.JLink.set_tif.assert_called_once()
    mock_jlink.JLink.flash_file.assert_called_once()
    mock_jlink.JLink.open.assert_called_once_with(serial_no=1234)
    mock_jlink.JLink.close.assert_called_once()
    mock_jlink.JLink.erase.assert_not_called()
