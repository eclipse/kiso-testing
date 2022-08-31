##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
UDS Auxiliary plugin
********************

:module: uds_auxiliary

:synopsis: implementation of existing UdsAuxiliary for Robot
    framework usage.

.. currentmodule:: uds_auxiliary

"""

from typing import List, Optional, Union

from robot.api import logger
from robot.api.deco import keyword, library
from uds import IsoServices

from pykiso.lib.robot_framework.aux_interface import RobotAuxInterface

from ..auxiliaries.udsaux.common.uds_response import UdsResponse
from ..auxiliaries.udsaux.uds_auxiliary import UdsAuxiliary as UdsAux


@library(version="0.1.0")
class UdsAuxiliary(RobotAuxInterface):
    """Robot framework plugin for UdsAuxiliary."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        """Initialize attributes."""
        super().__init__(aux_type=UdsAux)

    @keyword(name="Send uds raw")
    def send_uds_raw(
        self,
        msg_to_send: bytes,
        aux_alias: str,
        timeout_in_s: float = 6,
        response_required: bool = True,
    ) -> Union[list, bool]:
        """Send a UDS diagnostic request to the target ECU.

        :param msg_to_send: can uds raw bytes to be sent
        :param aux_alias: auxiliary's alias
        :param timeout_in_s: maximum time used to wait for a response.
        :param response_required: Wait for a response if True

        :return: the raw uds response's, or True if a response is
            not expected and the command is properly sent otherwise
            False
        """
        aux = self._get_aux(aux_alias)
        msg = aux.send_uds_raw(msg_to_send, timeout_in_s, response_required)
        return list(msg) if not isinstance(msg, bool) else msg

    @keyword(name="Send uds config")
    def send_uds_config(
        self, msg_to_send: dict, aux_alias: str, timeout_in_s: float = 6
    ) -> Union[dict, bool]:
        """Send UDS config to the target ECU.

        :param msg_to_send: uds config to be sent
        :param aux_alias: auxiliary's alias
        :param timeout_in_s: maximum time used to wait for a response

        :return: a dict containing the uds response, or True if a
            response is not expected and the command is properly sent
            otherwise False
        """
        msg_to_send["service"] = self.get_service_id(msg_to_send["service"])
        aux = self._get_aux(aux_alias)
        return aux.send_uds_config(msg_to_send, timeout_in_s)

    @keyword(name="Check raw response positive")
    def check_raw_response_positive(
        self, resp: UdsResponse, aux_alias: str
    ) -> Optional[bool]:
        """Check if the response is positive, raise an error if not

        :param resp: raw response of uds request

        :raise UnexpectedResponseError: raised when the answer is not the expected one

        :return: True if response is positive
        """
        aux = self._get_aux(aux_alias)
        return aux.check_raw_response_positive(resp)

    @keyword(name="Check raw response negative")
    def check_raw_response_negative(
        self, resp: UdsResponse, aux_alias: str
    ) -> Optional[bool]:
        """Check if the response is negative, raise an error if not

        :param resp: raw response of uds request

        :raise UnexpectedResponseError: raised when the answer is not the expected one

        :return: True if response is negative
        """
        aux = self._get_aux(aux_alias)
        return aux.check_raw_response_negative(resp)

    @keyword(name="Soft reset")
    def soft_reset(self, aux_alias: str) -> Union[dict, List[int]]:
        """Perform soft reset of the component, equivalent to a restart of application

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        return aux.soft_reset()

    @keyword(name="Hard reset")
    def hard_reset(self, aux_alias: str) -> Union[dict, List[int]]:
        """Allow power reset of the component

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        return aux.hard_reset()

    @keyword(name="Force ecu reset")
    def force_ecu_reset(self, aux_alias: str) -> List[int]:
        """Allow power reset of the component

        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        return aux.force_ecu_reset()

    @keyword(name="Read data")
    def read_data(self, parameter: str, aux_alias: str) -> Union[dict, bool]:
        """UDS config command that allow data reading

        :param parameter: data to be read
        :param aux_alias: auxiliary's alias

        :return: a dict with uds config response
        """
        aux = self._get_aux(aux_alias)
        return aux.read_data(parameter)

    @keyword(name="Write data")
    def write_data(
        self, parameter: str, value: Union[List[bytes], bytes], aux_alias: str
    ) -> Union[dict, bool]:
        """UDS config command that allow data reading

        :param parameter: data to be read
        :param value: new content of the data
        :param aux_alias: auxiliary's alias

        :return: a dict with uds config response
        """
        aux = self._get_aux(aux_alias)
        return aux.write_data(parameter, value)

    @keyword(name="Start tester present with ${period} seconds ${aux_alias} ")
    def start_tester_present_sender(self, aux_alias, period: int = 4) -> None:
        """Start to continuously sends tester present messages via UDS

        :param period: period in seconds to use for the cyclic sending of tester present
        :param aux_alias: auxiliary's alias
        """
        aux = self._get_aux(aux_alias)
        aux.start_tester_present_sender(period)

    @keyword(name="Stop tester present")
    def stop_tester_present_sender(self, aux_alias) -> None:
        """Stop to continuously sends tester present messages via UDS"""
        aux = self._get_aux(aux_alias)
        aux.stop_tester_present_sender()

    @staticmethod
    def get_service_id(service_name: str) -> int:
        """Return the uds service id.

        :param service_name: service's name (EcuReset,
            ReadDataByIdentifier ...)

        :return: corresponding service identification number
        """
        try:
            service_id = IsoServices[service_name].value
        except KeyError:
            logger.error(f"{service_name} doesn't exist", html=True)
            raise KeyError(f"{service_name} doesn't exist")

        return service_id
