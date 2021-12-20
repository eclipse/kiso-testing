##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Record Auxiliary
****************
:module: record_auxiliary

:synopsis: Auxiliary used to record a connectors receive channel.

.. currentmodule:: record_auxiliary

"""
import logging
import threading

from pykiso import CChannel, SimpleAuxiliaryInterface

log = logging.getLogger(__name__)


class RecordAuxiliary(SimpleAuxiliaryInterface):
    """Auxiliary used to record a connectors receive channel"""

    def __init__(
        self,
        com: CChannel,
        is_active: bool = False,
        timeout: float = 0,
        **kwargs,
    ):
        """Constructor

        :param com: Communication connector to record
        :param is_active: Flag to actively poll receive channel in another thread
        :param timeout: timeout for the receive channel
        """
        super().__init__(**kwargs)
        self.channel = com
        self.is_active = is_active
        self.timeout = timeout
        self.receive_thread = threading.Thread(target=self.receive)
        self.stop_receive_event = threading.Event()

    def _create_auxiliary_instance(self) -> bool:
        """Open the connector and start running receive thread
        if is_active is set.

        :return: True if successful
        """

        log.info("Create auxiliary instance")
        log.info("Enable channel")

        try:
            if self.is_active:
                self.receive_thread.start()
                log.debug("receive thread started..")
            else:
                self.channel.open()

        except Exception:
            log.exception("Error encountered during channel creation.")
            return False
        return True

    def _delete_auxiliary_instance(self) -> bool:
        """Close connector and stop receive thread when is_active flag is set.

        :return: always True
        """
        log.info("Delete auxiliary instance")

        if self.receive_thread.is_alive():
            self.stop_receive_event.set()
            self.receive_thread.join()
            log.debug("receive thread stopped..")

        else:
            try:
                self.channel.close()
            except Exception:
                log.exception("Unable to close Channel.")

        return True

    def receive(self) -> None:
        """Open channel and actively poll the connectors receive channel.
        Stop and close connector when stop receive event has been set.
        """

        try:
            self.channel.open()
        except Exception:
            log.exception("Error encountered during channel creation.")
            return

        while not self.stop_receive_event.is_set():
            self.channel.cc_receive(timeout=self.timeout, raw=True)

        try:
            self.channel.close()
        except Exception:
            log.exception("Error encountered during closing channel.")
