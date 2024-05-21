from pathlib import Path

# Import pykiso
import pykiso

# Load the test environment configuration
pykiso.load_config(Path(__file__).parent.resolve() / "serial.yaml")

# From the pykiso library, import the type of auxiliary you defined in the configuration
# Here, it would be the CommunicationAuxiliary class
from pykiso.lib.auxiliaries.communication_auxiliary import CommunicationAuxiliary


def first_test():
    """Ping-pong test between sender and receiver (with no context manager)
    """
    # Get the instance of the sender and receiver defined in the configuration
    sender = CommunicationAuxiliary.get_instance('com_aux_sender')
    receiver = CommunicationAuxiliary.get_instance('com_aux_receiver')
    # Start the sender and receiver
    sender.start()
    receiver.start()
    # Use the auxiliaries for my test
    sender.send_message("Hello, World!")
    assert receiver.receive_message(timeout_in_s = 2) == "Hello, World!"
    print("Test passed!")
    # Stop the sender and receiver
    sender.stop()
    receiver.stop()

def second_test():
    """Ping-pong test between sender and receiver (with context manager)
    """
    # Get the instance of the sender and receiver defined in the configuration
    sender = CommunicationAuxiliary.get_instance('com_aux_sender')
    receiver = CommunicationAuxiliary.get_instance('com_aux_receiver')
    # Start the auxiliaries with a context manager
    with sender as sender, receiver as receiver:
        # Use the auxiliaries for my test
        sender.send_message("Hello, World!")
        assert receiver.receive_message(timeout_in_s = 2) == "Hello, World!"
    print("Second test passed!")

if __name__ == "__main__":
    first_test()
    second_test()
