"""
CommunicationAuxiliary
**************************

:module: communication_auxiliary

:synopsis: Auxiliary used to send raw bytes via a connector instead of pykiso.Messages

.. currentmodule:: communication_auxiliary

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

"""

import logging

from pykiso import AuxiliaryInterface
from pykiso import CChannel
from pykiso import Message


class CommunicationAuxiliary(AuxiliaryInterface):
    """ Auxiliary used to send raw bytes via a connector instead of pykiso.Messages"""

    def __init__(self, com: CChannel, **kwargs):
        """constructor

        :param com: CChannel that supports raw communication """
        super(CommunicationAuxiliary, self).__init__(**kwargs)
        self.channel = com

    def send_message(self, raw_msg: bytes):
        """ send a raw message (bytes) via the communication channel
        :param raw_msg: message to send"""
        return self.run_command("send", raw_msg, timeout_in_s=None)

    def receive_message(
        self, blocking: bool = True, timeout_in_s: float = None
    ) -> bytes:
        """ receive a raw message (bytes)

        :param blocking: wait for message till timeout elapses?
        :param timeout_in_s: how longto wait

        :returns: raw message"""

        logging.debug(
            f"retrieving message in {self} (blocking={blocking}, timeout={timeout_in_s})"
        )
        msg = self.wait_and_get_report(blocking=blocking, timeout_in_s=timeout_in_s)
        logging.debug(f"retrieved message '{msg}' in {self}")
        return msg

    def _create_auxiliary_instance(self):
        logging.info("Create auxiliary instance")
        logging.info("Enable channel")
        self.channel.open()
        return True

    def _delete_auxiliary_instance(self):
        logging.info("Delete auxiliary instance")
        # Close the communication with it
        self.channel.close()
        return True

    def _run_command(self, cmd_message: bytes, cmd_data: bytes = None):
        if cmd_message == "send":
            try:
                self.channel.cc_send(cmd_data, raw=True, timeout=1)
                return True
            except Exception:
                logging.exception(
                    f"encountered error while sending message '{cmd_data}' to {self.channel}"
                )
        elif isinstance(cmd_message, Message):
            logging.debug(f"ignored command '{cmd_message} in {self}'")
            return True
        else:
            logging.warning(f"received unkown command '{cmd_message} in {self}'")
        return False

    def _abort_command(self):
        """ no-op since we don't wait for ACKs """
        pass

    def _receive_message(self, timeout_in_s):
        """ no-op since it's handled in _run_command """
        try:
            rcv_data = self.channel.cc_receive(timeout=0, raw=True)
            logging.debug(f"received message '{rcv_data}' from {self.channel}")
            return rcv_data
        except Exception:
            logging.exception(
                f"encountered error while receiving message via {self.channel}"
            )
