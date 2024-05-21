from pathlib import Path

import pytest

import pykiso
from pykiso.lib.auxiliaries.acroname_auxiliary import AcronameAuxiliary
from pykiso.lib.auxiliaries.communication_auxiliary import CommunicationAuxiliary


def test_verify_pykiso_2_import_mechanism():
    # Load verification
    pykiso.load_config(Path(__file__).parent.resolve() / "dummy_serial.yaml")
    sender = CommunicationAuxiliary.get_instance('com_aux_sender')
    receiver = CommunicationAuxiliary.get_instance('com_aux_receiver')
    # Content verification
    with sender as sender, receiver as receiver:
        sender.send_message("Hello, World!")
        assert receiver.receive_message() == "Hello, World!"
    # Cleanup
    pykiso.ConfigRegistry.delete_aux_con()


def test_verify_pykiso_2_get_no_instance():
    pykiso.load_config(Path(__file__).parent.resolve() / "dummy_serial.yaml")
    assert CommunicationAuxiliary.get_instance('com_aux_sender') != None
    # No existing instance
    with pytest.raises(ValueError):
        CommunicationAuxiliary.get_instance('com_aux_receiver2')
    # Instance with the wrong type
    with pytest.raises(ValueError):
        AcronameAuxiliary.get_instance('com_aux_receiver')
    # Cleanup
    pykiso.ConfigRegistry.delete_aux_con()
