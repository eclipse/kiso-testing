##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
from pathlib import Path
from unittest.mock import MagicMock, call
from xml.etree.ElementTree import Element, ElementTree

import pytest

from pykiso.lib.auxiliaries.udsaux.common.odx_parser import OdxParser


def odx_content():
    odx = """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ODX MODEL-VERSION="2.1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
    <DIAG-LAYER-CONTAINER>
        <PROTOCOLS>
            <PROTOCOL ID="1">
                <SHORT-NAME>CAN_FD</SHORT-NAME>
                <LONG-NAME>CAN FD</LONG-NAME>
                <COMPARAM-SPEC-REF ID-REF="ISO_15765_3_on_ISO_15765_2" DOCREF="ISO_15765_3_on_ISO_15765_2" DOCTYPE="COMPARAM-SPEC"/>
            </PROTOCOL>
        </PROTOCOLS>
        <BASE-VARIANTS>
            <BASE-VARIANT ID="ECUXXX">
                <SHORT-NAME>ECUxxx</SHORT-NAME>
                <LONG-NAME>ECUxxx</LONG-NAME>
                <DIAG-DATA-DICTIONARY-SPEC>
                    <DATA-OBJECT-PROPS>
                        <DATA-OBJECT-PROP ID="3">
                            <SHORT-NAME>Software_Version</SHORT-NAME>
                            <LONG-NAME>Software_Version</LONG-NAME>
                            <COMPU-METHOD>
                                <CATEGORY>IDENTICAL</CATEGORY>
                            </COMPU-METHOD>
                            <DIAG-CODED-TYPE BASE-TYPE-ENCODING="ISO-8859-1" BASE-DATA-TYPE="A_ASCIISTRING" xsi:type="STANDARD-LENGTH-TYPE">
                                <BIT-LENGTH>128</BIT-LENGTH>
                            </DIAG-CODED-TYPE>
                            <PHYSICAL-TYPE BASE-DATA-TYPE="A_UNICODE2STRING"/>
                        </DATA-OBJECT-PROP>
                    </DATA-OBJECT-PROPS>
                    <STRUCTURES>
                        <STRUCTURE>
                        </STRUCTURE>
                    </STRUCTURES>
                </DIAG-DATA-DICTIONARY-SPEC>
                <DIAG-COMMS>
                    <DIAG-SERVICE ID="6" SEMANTIC="IDENTIFICATION">
                        <SHORT-NAME>SoftwareVersion_Read</SHORT-NAME>
                        <LONG-NAME>SoftwareVersion Read</LONG-NAME>
                        <SDGS>
                            <SDG>
                                <SDG-CAPTION ID="7">
                                    <SHORT-NAME>CANdelaServiceInformation</SHORT-NAME>
                                </SDG-CAPTION>
                                <SD SI="DiagInstanceQualifier">SoftwareVersion</SD>
                                <SD SI="DiagInstanceName">SoftwareVersion</SD>
                                <SD SI="ServiceQualifier">Read</SD>
                                <SD SI="ServiceName">Read</SD>
                                <SD SI="PositiveResponseSuppressed">no</SD>
                            </SDG>
                        </SDGS>
                        <AUDIENCE IS-SUPPLIER="false" IS-DEVELOPMENT="false" IS-MANUFACTURING="false" IS-AFTERSALES="false" IS-AFTERMARKET="false"/>
                        <REQUEST-REF ID-REF="9"/>
                        <POS-RESPONSE-REFS>
                            <POS-RESPONSE-REF ID-REF="10"/>
                        </POS-RESPONSE-REFS>
                        <NEG-RESPONSE-REFS>
                            <NEG-RESPONSE-REF ID-REF="11"/>
                        </NEG-RESPONSE-REFS>
                    </DIAG-SERVICE>
                </DIAG-COMMS>
                <REQUESTS>
                    <REQUEST ID="9">
                        <SHORT-NAME>RQ_SoftwareVersion_Read</SHORT-NAME>
                        <LONG-NAME>RQ SoftwareVersion Read</LONG-NAME>
                        <PARAMS>
                            <PARAM SEMANTIC="SERVICE-ID" xsi:type="CODED-CONST">
                                <SHORT-NAME>SID_RQ</SHORT-NAME>
                                <LONG-NAME>SID-RQ</LONG-NAME>
                                <BYTE-POSITION>0</BYTE-POSITION>
                                <CODED-VALUE>34</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>8</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                            <PARAM SEMANTIC="ID" xsi:type="CODED-CONST">
                                <SHORT-NAME>RecordDataIdentifier</SHORT-NAME>
                                <LONG-NAME>Identifier</LONG-NAME>
                                <BYTE-POSITION>1</BYTE-POSITION>
                                <CODED-VALUE>42069</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>16</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                        </PARAMS>
                    </REQUEST>
                </REQUESTS>
                <POS-RESPONSES>
                    <POS-RESPONSE ID="10">
                        <SHORT-NAME>PR_SoftwareVersion_Read</SHORT-NAME>
                        <LONG-NAME>PR SoftwareVersion Read</LONG-NAME>
                        <PARAMS>
                            <PARAM SEMANTIC="SERVICE-ID" xsi:type="CODED-CONST">
                                <SHORT-NAME>SID_PR</SHORT-NAME>
                                <LONG-NAME>SID-PR</LONG-NAME>
                                <BYTE-POSITION>0</BYTE-POSITION>
                                <CODED-VALUE>98</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>8</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                            <PARAM SEMANTIC="ID" xsi:type="CODED-CONST">
                                <SHORT-NAME>RecordDataIdentifier</SHORT-NAME>
                                <LONG-NAME>Identifier</LONG-NAME>
                                <BYTE-POSITION>1</BYTE-POSITION>
                                <CODED-VALUE>42069</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>16</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                            <PARAM SEMANTIC="DATA" xsi:type="VALUE">
                                <SHORT-NAME>SoftwareVersion</SHORT-NAME>
                                <LONG-NAME>SoftwareVersion</LONG-NAME>
                                <BYTE-POSITION>3</BYTE-POSITION>
                                <DOP-REF ID-REF="3"/>
                            </PARAM>
                        </PARAMS>
                    </POS-RESPONSE>
                </POS-RESPONSES>
                <NEG-RESPONSES>
                    <NEG-RESPONSE ID="11">
                        <SHORT-NAME>NR_SoftwareVersion_Read</SHORT-NAME>
                        <LONG-NAME>NR SoftwareVersion Read</LONG-NAME>
                        <PARAMS>
                            <PARAM SEMANTIC="SERVICE-ID" xsi:type="CODED-CONST">
                                <SHORT-NAME>SID_NR</SHORT-NAME>
                                <LONG-NAME>SID-NR</LONG-NAME>
                                <BYTE-POSITION>0</BYTE-POSITION>
                                <CODED-VALUE>127</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>8</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                            <PARAM SEMANTIC="SERVICEIDRQ" xsi:type="CODED-CONST">
                                <SHORT-NAME>SIDRQ_NR</SHORT-NAME>
                                <LONG-NAME>SIDRQ-NR</LONG-NAME>
                                <BYTE-POSITION>1</BYTE-POSITION>
                                <CODED-VALUE>34</CODED-VALUE>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>8</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                            <PARAM SEMANTIC="DATA" xsi:type="VALUE">
                                <SHORT-NAME>Read</SHORT-NAME>
                                <LONG-NAME>Read</LONG-NAME>
                                <BYTE-POSITION>2</BYTE-POSITION>
                                <DOP-REF ID-REF="13"/>
                            </PARAM>
                            <PARAM SEMANTIC="DATA" xsi:type="NRC-CONST">
                                <SHORT-NAME>NRCConst_Read</SHORT-NAME>
                                <LONG-NAME>Read</LONG-NAME>
                                <BYTE-POSITION>2</BYTE-POSITION>
                                <CODED-VALUES>
                                    <CODED-VALUE>19</CODED-VALUE>
                                    <CODED-VALUE>20</CODED-VALUE>
                                    <CODED-VALUE>34</CODED-VALUE>
                                    <CODED-VALUE>49</CODED-VALUE>
                                    <CODED-VALUE>51</CODED-VALUE>
                                </CODED-VALUES>
                                <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                                    <BIT-LENGTH>8</BIT-LENGTH>
                                </DIAG-CODED-TYPE>
                            </PARAM>
                        </PARAMS>
                    </NEG-RESPONSE>
                </NEG-RESPONSES>
                <GLOBAL-NEG-RESPONSES>
                    <GLOBAL-NEG-RESPONSE ID="14">
                    </GLOBAL-NEG-RESPONSE>
                </GLOBAL-NEG-RESPONSES>
            </BASE-VARIANT>
        </BASE-VARIANTS>
    </DIAG-LAYER-CONTAINER>
</ODX>
    """
    return odx


@pytest.fixture
def tmp_odx_file(tmp_path):
    odx_file = tmp_path / "odx_example.odx"
    xml = odx_content().strip()
    odx_file.write_text(xml)
    return odx_file


def test_constructor(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)

    assert isinstance(odx_parser.odx_tree, ElementTree)


def test__find_element_by_odx_id(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    odx_id = "6"
    element = odx_parser._find_element_by_odx_id(odx_id)

    assert isinstance(element, Element)
    assert element.attrib["ID"] == odx_id


def test__find_element_by_odx_id_not_found(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    odx_id = "1337"
    with pytest.raises(ValueError, match=f"No element with id={odx_id} found"):
        element = odx_parser._find_element_by_odx_id(odx_id)


def test__find_diag_service_by_sd(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    sd_name = "SoftwareVersion"
    elements = odx_parser._find_diag_services_by_sd(sd_name)
    for element in elements:
        assert isinstance(element, Element)
        assert element.tag == "DIAG-SERVICE"


def test__find_diag_service_by_sd_not_found(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    sd_name = "HardwareVersion"
    with pytest.raises(
        ValueError, match=f"No DIAG-SERVICE has a SD containing {sd_name}"
    ):
        element = odx_parser._find_diag_services_by_sd(sd_name)


def test_get_coded_values(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    expected_values = [34, 42069]
    coded_values = odx_parser.get_coded_values("SoftwareVersion", 34)
    assert coded_values == expected_values


def test_get_coded_values_failure(tmp_odx_file):
    odx_parser = OdxParser(tmp_odx_file)
    sw_version = "SoftwareVersion"
    sid = 46
    with pytest.raises(
        ValueError,
        match=f"Could not create request for service={sid} and sd={sw_version}",
    ):
        coded_values = odx_parser.get_coded_values(sw_version, sid)
