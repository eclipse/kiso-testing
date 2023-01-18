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

.. currentmodule:: odx_parser

"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

log = logging.getLogger(__name__)


class OdxParser:
    def __init__(self, odx_file: Path) -> None:
        with open(odx_file) as odx:
            # create a xml tree from root <ODX>
            self.odx_tree = ElementTree.parse(odx)

    def _find_element_by_odx_id(self, odx_id: str) -> Element:
        """Find an odx element by the given id

        :id: odx id of the element to search for
        :raises ValueError: if no element with given odx id found
        :return: the element with the given odx id
        """
        # xpath finding the element with the given id
        element = self.odx_tree.find(f".//*[@ID='{odx_id}']")
        if element is None:
            raise ValueError(f"No element with id={odx_id} found")
        return element

    def _find_diag_service_by_sd(self, sd_instance_name: str) -> Element:
        """Find the <DIAG-SERVICE> with the given sd_instance_name

        :sd_instance_name: content of the <SD SI="DiagInstanceName">
        :return: the parent diag service odx element of the sd element with given name
        """
        # xpath to diag service for given sd instance name
        diag_service = self.odx_tree.find(f".//SD[@SI][.='{sd_instance_name}']../../..")
        if diag_service is None:
            raise ValueError(f"No DIAG-SERVICE has a SD containing {sd_instance_name}")
        log.internal_debug(
            f"Found {diag_service}, short-name={diag_service.find('SHORT-NAME').text}"
        )
        return diag_service

    def get_coded_values_by_sd(self, sd: str) -> List[int]:
        """Get the list of coded values for a ODX request element to construct a UDS request from

        :sd: sd instance name
        :return: a list of the coded values to be converted into a uds request
        """
        log.internal_debug("Parsing coded values for request sd")
        diag_service = self._find_diag_service_by_sd(sd)
        request_id = diag_service.find(".//REQUEST-REF").attrib["ID-REF"]
        request_element = self._find_element_by_odx_id(request_id)
        coded_value_elements = request_element.findall(".//CODED-VALUE")
        coded_values = [int(coded_value.text) for coded_value in coded_value_elements]
        return coded_values

    def create_negative_response(sid, nrc):
        # sid from request
        # nrc from dict
        pass
