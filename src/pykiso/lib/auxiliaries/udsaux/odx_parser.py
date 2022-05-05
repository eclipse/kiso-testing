##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
odx_parser
**********

:module: odx_parser

:synopsis: A parser for Open Diagnostics eXchange (ODX) format.

.. currentmodule:: odx_parser

"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, NewType, Union

ServiceId = NewType("ServiceId", str)
DataId = NewType("DataId", str)
SubfunctionId = NewType("SubfunctionId", str)


class OdxParser:

    service_id_to_name = {
        0x10: "diagnosticSessionControl",
        0x11: "ecuReset",
        0x14: "clearDTC",
        0x19: "readDTC",
        0x22: "readDataByIdentifier",
        0x27: "securityAccess",
        0x2E: "writeDataByIdentifier",
        0x2F: "inputOutputControl",
        0x31: "routineControl",
        0x34: "requestDownload",
        0x35: "requestUpload",
        0x36: "transferData",
        0x37: "transferExit",
        0x3E: "testerPresent",
    }

    def __init__(
        self, odx_file_path: Union[str, Path], **services: Dict[int, str]
    ) -> None:
        self.odx_file = odx_file_path
        self.services = {**self.service_id_to_name, **services}
        self.service_configuration = defaultdict(dict)
        self._xml_elements = {}

    def parse(self) -> Dict[ServiceId, Dict[Union[DataId, SubfunctionId], Any]]:

        root = ET.parse(self.odx_file)

        self._xml_elements = {
            child.attrib["ID"]: child
            for child in root.iter()
            if child.attrib.get("ID") is not None
        }

        for value in self._xml_elements.values():
            if value.tag != "DIAG-SERVICE":
                continue

            did_config = {}

            sdg = value.find("SDGS").find("SDG")
            for sd in sdg:
                if sd.attrib.get("SI") == "DiagInstanceName":
                    did_config["DID_Name"] = sd.text
                    did_config["DID"] = []

            request_id = value.find("REQUEST-REF").attrib["ID-REF"]
            request_element = self._xml_elements[request_id]
            request_params = request_element.find("PARAMS")

            self._parse_request(request_params, did_config)

            if value.attrib.get("TRANSMISSION-MODE") != "SEND-ONLY":
                positive_response_id = (
                    value.find("POS-RESPONSE-REFS")
                    .find("POS-RESPONSE-REF")
                    .attrib["ID-REF"]
                )
                positive_response_element = self._xml_elements[positive_response_id]

            positive_response_params = positive_response_element.find("PARAMS")

            self._parse_positive_response(positive_response_params, did_config)

        return self.service_configuration

    def _parse_request(
        self, odx_request_params: ET.Element, did_config: Dict[str, Any]
    ):
        """Parse the UDS requests information of the ODX file.

        :param odx_request_params: _description_
        :param did_config: _description_
        """
        uds_request = list()

        for request_param in odx_request_params:
            semantic = request_param.attrib.get("SEMANTIC")

            if semantic is None:
                continue

            elif semantic == "SERVICE-ID":
                service_id = int(request_param.find("CODED-VALUE").text)
                uds_request.append(service_id)
                did_config["SID"] = service_id
                did_config["SID_name"] = self.service_id_to_name.get(service_id)

                service_name = self.service_id_to_name.get(service_id)

                if service_name is None:
                    continue
                elif service_name not in self.service_configuration:
                    self.service_configuration[service_name] = {
                        did_config["DID_Name"]: {service_name: []}
                    }

            elif semantic == "SUBFUNCTION":
                subId = int(request_param.find("CODED-VALUE").text)
                did_config["SubID"] = subId
                uds_request.append(subId)

            elif semantic == "ID":
                data = int(request_param.find("CODED-VALUE").text)
                dataLength = int(
                    int(request_param.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text)
                    / 8
                )
                dataId = []
                for param in range(0, dataLength):
                    dataId.append((data >> (8 * (dataLength - param - 1))) & 0xFF)
                did_config["DID"].extend(dataId)
                uds_request.extend(dataId)

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

        did_config["UdsRequest"] = uds_request
        self.service_configuration[service_name][did_config["DID_Name"]] = did_config

    def _parse_positive_response(
        self, odx_positive_response_params: ET.Element, did_config: Dict[str, Any]
    ):
        reponse_length = 0
        subfunction_id = None

        for param in odx_positive_response_params:

            semantic = param.attrib.get("SEMANTIC")
            if semantic is None:
                continue

            start_byte = int(param.find("BYTE-POSITION").text)

            if semantic == "SERVICE-ID":
                # expected service ID
                response_sid = int(param.find("CODED-VALUE").text)
                service_name = self.service_id_to_name.get(response_sid - 0x40)
                service_bit_length = int(
                    (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                )
                byte_length = (service_bit_length + 7) // 8
                # keep in case it could be useful in future
                # service ID start
                # responseIdStart = start_byte

                # keep in case it could be useful in future
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
        resp_list.extend([response_sid])
        resp_list.extend(subfunction_id)
        resp_list.extend([0] * (reponse_length - len(resp_list)))

        self.service_configuration[service_name][did_config["DID_Name"]][
            "UdsResponse"
        ] = resp_list
