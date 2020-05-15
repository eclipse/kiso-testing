import pytest
from pykiso.lib.connectors.flash_jlink import JLinkFlasher
from pykiso.lib.connectors.flash_jlink import pylink


@pytest.fixture
def mock_jlink(mocker):
    """
    replace pylink.JLink and pylink.Library with mocks
    """

    class MockJLink:
        def __init__(self, lib, **kwargs):
            pass

        connect = mocker.stub(name="connect")
        flash_file = mocker.stub(name="flash_file")
        _finalize = mocker.stub(name="_finalize")

    class MockJLib:
        def __init__(self, lib=None):
            pass

    mocker.patch.object(pylink, "JLink", new=MockJLink)
    mocker.patch.object(pylink, "Library", new=MockJLib)
    return pylink


def test_jlink_flasher(tmp_file, mock_jlink):
    """ assert that the correct library functions are called """
    with JLinkFlasher(tmp_file) as fl:
        fl.flash()
    mock_jlink.JLink.connect.assert_called_once()
    mock_jlink.JLink.flash_file.assert_called_once()
    mock_jlink.JLink._finalize.assert_called_once()
