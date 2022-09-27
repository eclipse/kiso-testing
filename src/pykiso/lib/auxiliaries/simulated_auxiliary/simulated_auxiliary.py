##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Simulated Auxiliary
*******************

:module: simulated_auxiliary

:synopsis: auxiliary used to simulate a virtual Device Under Test(DUT)

.. currentmodule:: simulated_auxiliary
"""

import itertools
import logging

from pykiso import AuxiliaryInterface, message

from .simulation import Simulation

ACK = message.MessageType.ACK
ABORT = message.MessageCommandType.ABORT
PING = message.MessageCommandType.PING

log = logging.getLogger(__name__)


class SimulatedAuxiliary(AuxiliaryInterface):
    """Custom auxiliary use to simulate a virtual DUT."""

    def __init__(self, com=None, **kwargs):
        """Initialize attributes.

        :param com: configured channel
        """
        super().__init__(**kwargs)
        self.channel = com
        self.context = Simulation()
        self.playbook = None
        self.ts_tc = None
        log.internal_debug(f"com is {com}")

    def _create_auxiliary_instance(self) -> bool:
        """Open current associated channel.

        :return: always True
        """
        log.internal_info("Create auxiliary instance")
        log.internal_info("Enable channel")
        self.channel.open()
        return True

    def _delete_auxiliary_instance(self) -> bool:
        """Close current associated channel.

        :return: always True
        """
        log.internal_info("Delete auxiliary instance")
        self.channel.close()
        return True

    def _run_command(
        self, cmd_message: message.Message, cmd_data: bytes = None
    ) -> None:
        """Not used."""
        pass

    def _abort_command(self) -> None:
        """Not used."""
        pass

    def _receive_message(self, timeout_in_s: float) -> message.Message or None:
        """Read current received message from the associated channel
        and play a pre-configured scenario depending on message
        test suite and case number.

        :param timeout_in_s: timeout applied on receive event.

        :return: Message if successful, otherwise None
        """
        responses = []

        recv_response = self.channel.cc_receive(timeout_in_s)

        msg = recv_response.get("msg")

        # don't advance simulation if no message or ACK has been received
        if msg is None or msg.msg_type == ACK:
            return msg

        # if message is PING, respond accordingly
        if msg.sub_type == PING:
            responses = next(iter(self.context.handle_ping_pong()))
            self._send_responses(responses(msg))
            return msg

        # determine pre-defined scenario if ts/tc changes
        # the ABORT command always comes with ts=0, tc=0, but we still want to
        # advance the playbook.
        if msg.sub_type != ABORT and (msg.test_suite, msg.test_case) != self.ts_tc:
            self.ts_tc = msg.test_suite, msg.test_case
            cur_scenario = self.context.get_scenario(*self.ts_tc)
            # cycle creates an iterator and makes it possible to replay the current
            # playbook.
            self.playbook = itertools.cycle(cur_scenario)

        play = next(self.playbook)
        responses = play(msg) if play is not None else []
        self._send_responses(responses)

        return msg

    def _send_responses(self, responses: message.Message) -> None:
        """Send response over CChannel.

        :param responses: TestApp protocol message type(ack, abort...)
        """
        for response in responses:
            self.channel._cc_send(msg=response)
