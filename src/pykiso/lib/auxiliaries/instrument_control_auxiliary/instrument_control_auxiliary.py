##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Instrument Control Auxiliary
****************************

:module: instrument_control_auxiliary

:synopsis: Auxiliary used to communicate via a VISA connector using the
    SCPI protocol.

.. currentmodule:: instrument_control_auxiliary

"""
import logging
import queue
import re
import time
from typing import Any, List, Optional, Tuple, Union

from pykiso import CChannel
from pykiso.interfaces.dt_auxiliary import (
    DTAuxiliaryInterface,
    close_connector,
)

from .lib_scpi_commands import LibSCPI

log = logging.getLogger(__name__)


class InstrumentControlAuxiliary(DTAuxiliaryInterface):
    """Auxiliary used to communicate via a VISA connector using the SCPI
    protocol.
    """

    def __init__(
        self,
        com: CChannel,
        instrument="",
        write_termination="\n",
        output_channel: int = None,
        **kwargs,
    ):
        """Constructor.

        :param com: VISAChannel that supports VISA communication
        :param instrument: name of the instrument currently in use
            (will be used to adapt the SCPI commands)
        :param write_termination: write termination character
        :param output_channel: output channel to use on the instrument
            currently in use (if more than one)
        """
        super().__init__(
            is_proxy_capable=False, tx_task_on=False, rx_task_on=False, **kwargs
        )
        self.channel = com
        self.instrument = instrument
        self.write_termination = write_termination
        self.output_channel = output_channel
        self.helpers = LibSCPI(self, self.instrument)

    def write(
        self, write_command: str, validation: Tuple[str, Union[str, List[str]]] = None
    ) -> str:
        """Send a write request to the instrument.

        :param write_command: command to send
        :param validation: contain validation criteria apply on the
            response
        """
        log.internal_debug(f"Sending a write request in {self} for {write_command}")
        return self.handle_write(write_command, validation)

    def handle_write(
        self, write_command: str, validation: Tuple[str, Union[str, List[str]]] = None
    ) -> str:
        """Send a write request to the instrument and then returns if
        the value was successfully written. A query is sent immediately
        after the writing and the answer is compared to the expected
        one.

        :param write_command: write command to send
        :param validation: tuple of the form
            (validation command (str), expected output (str or list of str))

        :return: status message depending on the command validation:
            SUCCESS, FAILURE or NO_VALIDATION
        """
        log.internal_debug(f"Sending a write request in {self} for {write_command}")
        # Send the message with the termination character
        self.channel.cc_send(msg=write_command + self.write_termination)

        if validation is not None:
            # Check that the writing request was successfully performed on the instrument
            validation_query, validation_expected_output = validation
            if isinstance(validation_expected_output, str):
                validation_expected_output = [validation_expected_output]

            # Send the validation query with a delay between the previous write and this query request
            # to make sure that the instrument has had sufficient time to complete the operation
            time.sleep(0.1)
            validation_query_response = self.handle_query(validation_query)

            # Check that the responses matches the expected response
            if (
                isinstance(validation_query_response, str)
                and validation_query_response != ""
            ):
                # Check the tag VALUE{} in the expected output and adapt the validation process
                match = re.compile(r"VALUE{([+-]?\d+[\.\d]*)}").findall(
                    validation_expected_output[0]
                )
                if match:
                    # tag "VALUE{value}" detected. This tag can be used when we want to ensure that
                    # a numerical parameter was correctly set on the instrument
                    if float(match[0]) == float(validation_query_response.split()[0]):
                        write_success = True
                    else:
                        write_success = False
                else:
                    # compare the expected output with the result of the validation query command
                    if validation_query_response in validation_expected_output:
                        write_success = True
                    else:
                        write_success = False
                if write_success is True:
                    log.internal_debug(
                        f"Write request {write_command} successful after verification"
                    )
                    return "SUCCESS"
                else:
                    log.internal_warning(
                        f"Write request {write_command} failed! Validation query response was different than expected."
                    )
                    return "FAILURE"
            else:
                log.internal_warning(
                    f"Write request {write_command} failed! No response received for the validation query."
                )
                return "FAILURE"
        else:
            log.internal_debug(
                f"Write request {write_command} processed without validation"
            )
            return "NO_VALIDATION"

    def read(self) -> Union[str, bool]:
        """Send a read request to the instrument.

        :return: received response from instrument otherwise empty
            string
        """
        log.internal_debug(f"Sending a read request in {self}")
        return self.handle_read()

    def handle_read(self) -> Optional[str]:
        """Handle read command by calling associated connector
        cc_receive.

        :return: received response from instrument otherwise empty
            string
        """
        response = self.channel.cc_receive()
        response_data = response.get("msg")
        if isinstance(response_data, bytes):
            response_data = response_data.decode().strip()
        return response_data

    def query(self, query_command: str) -> Union[bytes, str]:
        """Send a query request to the instrument. Uses the 'query' method of the
            channel if available, uses 'cc_send' and 'cc_receive' otherwise.

        :param query_command: query command to send

        :return: Response message, None if the request expired with a
            timeout.
        """
        log.internal_debug(f"Sending a query request in {self}) for {query_command}")
        return self.handle_query(query_command)

    def handle_query(self, query_command: str) -> Optional[str]:
        """Send a query request to the instrument. Uses the 'query' method of the
            channel if available, uses 'cc_send' and 'cc_receive' otherwise.

        :param query_command: query command to send

        :return: Response message, None if the request expired with a
            timeout.
        """
        if hasattr(self.channel, "query"):
            response = self.channel.query(query_command + self.write_termination)
            return response.get("msg")
        else:
            self.channel.cc_send(msg=query_command + self.write_termination)
            time.sleep(0.05)
            response = self.channel.cc_receive()
            response_data = response.get("msg")
            if isinstance(response_data, bytes):
                response_data = response_data.decode().strip()
            return response_data

    def _create_auxiliary_instance(self) -> bool:
        """Open the connector.

        :return: always True
        """
        log.internal_info("Create auxiliary instance")

        try:
            # Open instrument
            log.internal_info("Open instrument")
            self.channel.open()

            # Enable remote control
            log.internal_info("Enable remote control")
            command, validation = self.helpers.get_command(
                cmd_tag="REMOTE_CONTROL",
                cmd_type="write",
                cmd_validation=["REMOTE", "ON", "1"],
            )
            self.handle_write(f"{command} ON".strip(), validation)

            # Select channel if needed
            if self.output_channel is not None:
                log.internal_info(f"Select channel {self.output_channel}")
                command, validation = self.helpers.get_command(
                    cmd_tag="OUTPUT_CHANNEL",
                    cmd_type="write",
                    cmd_validation=f"{self.output_channel}",
                )
                self.handle_write(
                    f"{command} {self.output_channel}".strip(), validation
                )
            else:
                log.internal_info("Using default output channel.")
        except Exception:
            log.exception("Unable to safely open the instrument.")
            return False
        return True

    @close_connector
    def _delete_auxiliary_instance(self) -> bool:
        """Close the connector communication.

        :return: True if the connectors is closed otherwise False
        """
        log.internal_info("Auxiliary instance deleted")
        return True

    def _run_command(self, cmd_message: Any, cmd_data: Optional[bytes]) -> None:
        """Not used.

        Simply respect the interface.
        """

    def _receive_message(self, timeout_in_s: float) -> None:
        """Not used.

        Simply respect the interface.
        """
