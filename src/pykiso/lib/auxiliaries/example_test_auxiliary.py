##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Example Auxiliary
*****************

:module: example_test_auxiliary

:synopsis: Example auxiliary that simulates a normal test run without
    ever doing anything.

.. currentmodule:: example_test_auxiliary


.. warning:: Still under test
"""
import logging

# Import the framework modules
from pykiso import AuxiliaryInterface, message

log = logging.getLogger(__name__)


class ExampleAuxiliary(AuxiliaryInterface):
    """Example of an auxiliary implementation."""

    def __init__(
        self,
        name=None,
        com=None,
        flash=None,
        **kwargs,
    ) -> None:
        """Constructor.

        :param name: Alias of the auxiliary instance
        :param com: Communication connector
        :param flash: flash connector
        """
        super().__init__(name=name, **kwargs)
        self.channel = com
        self.flash = flash
        self.options = kwargs
        log.debug(f"com is {com}")
        log.debug(f"flash is {flash}")

    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel and send a ping command.

        :return: if channel creation is successful and ping command is
            answered return True otherwise False
        """
        log.info("Create auxiliary instance")
        # Create an instance (e.g. flash it) -> Placeholder
        # Enable the communication with it
        log.info("Enable channel")
        self.channel.open()
        # Pingpong
        return_code = self._send_and_wait_ack(message.Message(), 0.5, 2)
        # Return output
        return return_code

    def _delete_auxiliary_instance(self) -> bool:
        """Close the connector communication.

        :return: always True
        """
        log.info("Delete auxiliary instance")
        # Close the communication with it
        self.channel.close()
        return True

    def _run_command(
        self, cmd_message: message.Message, cmd_data: bytes = None
    ) -> bool:
        """Run the corresponding command.

        :param cmd_message: command type
        :param cmd_data: payload data to send over CChannel

        :return: True if ACK is received otherwise False
        """
        log.debug("Send test request: {}".format(cmd_message))
        return self._send_and_wait_ack(cmd_message, 0.5, 2)

    def _abort_command(self) -> bool:
        """Send an abort command and reset the auxiliary if needed.

        :return: True if ACK is received otherwise False
        """
        log.info("Send abort request")
        # Try a soft abort
        msg = message.Message(
            message.MessageType.COMMAND, message.MessageCommandType.ABORT
        )  # TODO verify if this generation can happened somewhere else
        result = self._send_and_wait_ack(msg, 0.5, 2)
        # If not successful, do hard reset
        if result is False:
            self._delete_auxiliary_instance()
            self._create_auxiliary_instance()
        return result

    def _receive_message(self, timeout_in_s: float) -> message.Message:
        """Get message from the device under test.

        :param timeout_in_s: Time in ms to wait for one try

        :return: receive message
        """
        # Read message on the channel
        recv_response = self.channel.cc_receive(timeout_in_s)
        received_message = recv_response.get("msg")

        if received_message is not None:
            # Send ack
            self.channel._cc_send(
                msg=received_message.generate_ack_message(message.MessageAckType.ACK)
            )
            # Return message
            return received_message

    def _send_and_wait_ack(
        self, message_to_send: message.Message, timeout: float, tries: int
    ) -> bool:
        """Send via the channel a message and wait for an acknowledgement.

        :param message_to_send: Message you want to send out
        :param timeout: Time in ms to wait for one try
        :param tries: Number of tries to send the message

        :return: True - Ack, False - Nack
        """
        number_of_tries = 0
        result = False

        while number_of_tries < tries:
            log.debug("Run send try n:" + str(number_of_tries))
            # Increase number of tries
            number_of_tries += 1
            # Send the message
            self.channel.cc_send(msg=message_to_send)
            # Wait until we get something back
            recv_response = self.channel.cc_receive(timeout)
            received_message = recv_response.get("msg")
            # Check the outcome
            if received_message is None:
                continue  # Next try will occur
            else:
                if message_to_send.check_if_ack_message_is_matching(received_message):
                    log.debug("{} sent".format(message_to_send))
                    result = True
                    break
                else:
                    log.warning(
                        "Received {} not matching {}!".format(
                            received_message, message_to_send
                        )
                    )
                    continue  # A NACK got received # TODO later on we should have "not supported" and ignore it than.
        # Must be ">" because number_of_tries is increased at the beginning of the while loop above
        if number_of_tries > tries:
            log.warning(
                f"Exceeded the number of tries ({tries}) for sending the message"
            )
        return result
