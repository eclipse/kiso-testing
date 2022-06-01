##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
ODX parser
**********

:module: odx_parser

:synopsis: A basic parser for Open Diagnostics eXchange (ODX) format.

.. currentmodule:: odx_parser

"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Union

from .uds_utils import SERVICE_ID_TO_NAME


class OdxParser:
    """A parser for ODX files that extracts the request and positive response
    information and stored it into the `service_configuration` attribute.
    """

    def __init__(
        self, odx_file_path: Union[str, Path], **services: Dict[int, str]
    ) -> None:
        self.odx_file = odx_file_path
        self.services = {**SERVICE_ID_TO_NAME, **services}
        self.service_configuration = defaultdict(dict)
        self._xml_elements = {}

    def parse(self) -> Dict[int, Dict[str, Any]]:
        """Parse an ODX file to extract the request and positive response information
        for each service.

        :return: the ODX file parsed as a dictionary.
        """
        root = ET.parse(self.odx_file)

        self._xml_elements = {
            child.attrib["ID"]: child
            for child in root.iter()
            if child.attrib.get("ID") is not None
        }

        for service_desc in self._xml_elements.values():
            if service_desc.tag != "DIAG-SERVICE":
                continue

            service_config = {}

            sdg = service_desc.find("SDGS").find("SDG")
            for sd in sdg:
                if sd.attrib.get("SI") == "DiagInstanceName":
                    service_config["DID_name"] = sd.text
                    service_config["DID"] = []

            request_id = service_desc.find("REQUEST-REF").attrib["ID-REF"]
            request_element = self._xml_elements[request_id]
            request_params = request_element.find("PARAMS")

            self._parse_request(request_params, service_config)

            if service_desc.attrib.get("TRANSMISSION-MODE") != "SEND-ONLY":
                positive_response_id = (
                    service_desc.find("POS-RESPONSE-REFS")
                    .find("POS-RESPONSE-REF")
                    .attrib["ID-REF"]
                )
                positive_response_element = self._xml_elements[positive_response_id]

            positive_response_params = positive_response_element.find("PARAMS")

            self._parse_positive_response(positive_response_params, service_config)

        return self.service_configuration

    def _parse_request(
        self, odx_request_params: ET.Element, service_config: Dict[str, Any]
    ):
        """Parse the UDS requests information from the ODX file.

        :param odx_request_params: XML description of the positive response
            elements from the loaded ODX.
        :param service_config: dictionary containing the information of the
            previously parsed data identifiers and subfunctions.
        """
        uds_request = list()

        for request_param in odx_request_params:
            semantic = request_param.attrib.get("SEMANTIC")

            if semantic is None:
                continue

            elif semantic == "SERVICE-ID":
                service_id = int(request_param.find("CODED-VALUE").text)
                uds_request.append(service_id)
                service_config["SID"] = service_id
                service_name = self.services.get(service_id)

                service_config["SID_name"] = service_name

                if service_name is None:
                    continue
                elif service_id not in self.service_configuration:
                    self.service_configuration[service_id] = {
                        service_config["DID_name"]: {service_name: []}
                    }

            elif semantic == "SUBFUNCTION":
                subfunction_id = int(request_param.find("CODED-VALUE").text)
                service_config["SubID"] = subfunction_id
                uds_request.append(subfunction_id)

            elif semantic == "ID":
                data = int(request_param.find("CODED-VALUE").text)
                data_length = int(
                    int(request_param.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text)
                    / 8
                )
                data_identifier = []
                for param_idx in range(1, data_length + 1):
                    data_identifier.append(
                        (data >> (8 * (data_length - param_idx))) & 0xFF
                    )
                service_config["DID"].extend(data_identifier)
                uds_request.extend(data_identifier)

            elif semantic == "DATA":
                data_object_prop = request_param.find("DOP-REF")
                if data_object_prop is None:
                    continue

                data_id = data_object_prop.attrib["ID-REF"]
                data_element = self._xml_elements[data_id]

                coded_type = data_element.find("DIAG-CODED-TYPE")

                if coded_type is not None:
                    data_bit_length = coded_type.find("BIT-LENGTH")

                    if data_bit_length is not None:
                        data_byte_length = (int(data_bit_length.text) + 7) // 8
                        uds_request.extend(data_byte_length * [0x00])
                        continue

                    data_byte_length = data_element.find("BYTE-SIZE")

                    if data_byte_length is not None:
                        data_byte_length = int(data_byte_length.text)
                        uds_request.extend(data_byte_length * [0x00])
                        continue

                param_length = 0

                struct_params = data_element.find("PARAMS")
                if struct_params is None:
                    param_length += 1
                    continue

                for struct_param in struct_params:
                    struct_param_key = struct_param.find("DOP-REF").attrib["ID-REF"]
                    struct_param_element = self._xml_elements[struct_param_key]

                    coded_type = struct_param_element.find("DIAG-CODED-TYPE")
                    if coded_type is not None:
                        data_bit_length = coded_type.find(
                            "BIT-LENGTH"
                        ) or coded_type.find("MIN-LENGTH")

                        if data_bit_length is not None:
                            param_length += (int(data_bit_length.text) + 7) // 8
                    else:
                        param_length += 1

                uds_request.extend(param_length * [0x00])

        service_config["request"] = uds_request
        self.service_configuration[service_id]["name"] = service_name
        self.service_configuration[service_id][
            service_config["DID_name"]
        ] = service_config

    def _parse_positive_response(
        self, odx_positive_response_params: ET.Element, service_config: Dict[str, Any]
    ):
        """Parse the UDS positive responses information from the ODX file.

        :param odx_request_params: XML description of the positive response
            elements from the loaded ODX.
        :param service_config: dictionary containing the information of the
            previously parsed data identifiers and subfunctions.
        """
        reponse_length = 0
        subfunction_id = None

        for param in odx_positive_response_params:

            semantic = param.attrib.get("SEMANTIC")
            if semantic is None:
                continue

            start_byte = int(param.find("BYTE-POSITION").text)

            if semantic == "SERVICE-ID":
                # expected service ID
                response_id = int(param.find("CODED-VALUE").text)
                service_id = response_id - 0x40
                service_bit_length = int(
                    (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                )
                byte_length = (service_bit_length + 7) // 8
                # keep in case it could be useful in future
                # service ID start
                # responseIdStart = start_byte
                # service ID end
                # responseIdEnd = start_byte + byte_length
                reponse_length += byte_length

            elif semantic == "SUBFUNCTION" or semantic == "ID":
                # expected subfunction ID
                subfunction_id = param.find("CODED-VALUE")
                subfunction_id = int(subfunction_id.text)
                subfunction_bit_length = int(
                    (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                )
                byte_length = int(subfunction_bit_length / 8)
                # subfunction ID start
                subfunction_start_byte = start_byte
                # subfunction ID end
                subfunction_end_byte = start_byte + byte_length
                reponse_length += byte_length

            elif semantic == "DATA":
                data_object_element = self._xml_elements[
                    (param.find("DOP-REF")).attrib["ID-REF"]
                ]
                if data_object_element.tag == "DATA-OBJECT-PROP":
                    # keep in case it could be useful in future
                    # start = int(param.find("BYTE-POSITION").text)
                    fixed_data_length = data_object_element.find(
                        "DIAG-CODED-TYPE"
                    ).find("BIT-LENGTH")
                    if fixed_data_length is None:
                        # has optional data
                        data_bit_length = 0
                    else:
                        data_bit_length = int(fixed_data_length.text)
                    byte_length = int(data_bit_length / 8)
                    reponse_length += byte_length
                elif data_object_element.tag == "STRUCTURE":
                    # keep in case it could be useful in future
                    # start = int(param.find("BYTE-POSITION").text)
                    if data_object_element.find("BYTE-SIZE") is not None:
                        byte_length = int(data_object_element.find("BYTE-SIZE").text)
                    else:
                        byte_length = 64
                    reponse_length += byte_length

        if subfunction_id is None:
            subfunction_id, subfunction_start_byte, subfunction_end_byte = 0, 0, 0

        sub_function_len = subfunction_end_byte - subfunction_start_byte

        subfunction_id = (
            list(subfunction_id.to_bytes(sub_function_len, byteorder="big"))
            if sub_function_len > 1
            else [subfunction_id]
        )

        resp_list = list()
        resp_list.extend([response_id])
        resp_list.extend(subfunction_id)
        resp_list.extend([0] * (reponse_length - len(resp_list)))

        self.service_configuration[service_id][service_config["DID_name"]][
            "response"
        ] = resp_list
