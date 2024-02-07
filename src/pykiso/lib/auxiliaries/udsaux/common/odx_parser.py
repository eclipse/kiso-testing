##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
"""
ODX Parser for UDS Server Auxiliary
***********************************

:module: odx_parser

:synopsis: odx parser used by a uds server to dynamically configure its
    uds callbacks from an odx file

.. currentmodule:: odx_parser

"""
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import List
from xml.etree.ElementTree import Element

# Use defusedxml, as xml is not secure against maliciously constructed data.
from defusedxml import ElementTree

log = logging.getLogger(__name__)


class OdxParser:
    """Used to parse ODX files to configure a Uds server"""

    class RefType(Enum):
        REQUEST = "REQUEST-REF"
        POS_RESPONSE = "POS-RESPONSE-REF"

    def __init__(self, odx_file: Path) -> None:
        with open(odx_file) as odx:
            # create a xml tree from root <ODX>
            self.odx_tree = ElementTree.parse(odx)

    def _find_element_by_odx_id(self, odx_id: str) -> Element:
        """Find an odx element by the given id

        :param id: odx id of the element to search for
        :raises ValueError: if no element with given odx id found
        :return: the element with the given odx id
        """
        # xpath finding the element with the given id
        element = self.odx_tree.find(f".//*[@ID='{odx_id}']")
        if element is None:
            raise ValueError(f"No element with id={odx_id} found")
        return element

    def _find_diag_services_by_sd(self, sd_instance_name: str) -> Element:
        """Find the <DIAG-SERVICE> with the given sd_instance_name

        :param sd_instance_name: content of the <SD SI="DiagInstanceName">
        :return: the parent diag service odx element of the sd element with given name
        """
        # xpath to diag service for given sd instance name
        diag_services = self.odx_tree.findall(f".//SD[@SI][.='{sd_instance_name}']../../..")
        if not diag_services:
            raise ValueError(f"No DIAG-SERVICE has a SD containing {sd_instance_name}")
        return diag_services

    def get_coded_values(self, sd: str, sid: int, ref_type: RefType = RefType.REQUEST) -> List[int]:
        """Get the list of coded values for a ODX request element to construct a UDS request from

        :param sd: sd instance name
        :param sid: service id to differentiate between diag services with the same sd name
        :raises ValueError: if no request could be created for the given sd name and SID
        :return: a list of the coded values to be converted into a uds request
        """
        diag_services = self._find_diag_services_by_sd(sd)
        for diag_service in diag_services:
            request_id = diag_service.find(f".//{ref_type.value}").attrib["ID-REF"]
            request_element = self._find_element_by_odx_id(request_id)
            # compare SIDs to differentiate between e.g. read and write request with same sd name
            request_sid = int(request_element.find(".//PARAM[@SEMANTIC='SERVICE-ID']/CODED-VALUE").text)
            if request_sid == sid:
                coded_value_elements = request_element.findall(".//CODED-VALUE")
                coded_values = [int(coded_value.text) for coded_value in coded_value_elements]
                return coded_values
        log.error(f"Could not create request for service={sid} and sd={sd}")
        raise ValueError(f"Could not create request for service={sid} and sd={sd}")
