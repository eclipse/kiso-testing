##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import unittest

import pykiso
from pykiso.test_result import xml_result


class MockTestResult:
    def __init__(self, test_ids, doc="") -> None:
        self.test_ids = test_ids
        self._testMethodDoc = doc


def test_TestInfo_custom_constructor(mocker):
    test_method = MockTestResult(test_ids={"Component1": ["Req"]}, doc="DOCS")
    mock_test_info = mocker.patch.object(
        xml_result.xmlrunner.result._TestInfo, "__init__"
    )

    custom_xml = xml_result.TestInfo(
        "test_result",
        test_method,
        "outcome",
        "err",
        "subTest",
        "filename",
        "lineno",
        "doc",
    )

    mock_test_info.assert_called_once_with(
        "test_result",
        test_method,
        "outcome",
        "err",
        "subTest",
        "filename",
        "lineno",
        "doc",
    )
    assert custom_xml.test_ids == '{"Component1": ["Req"]}'
    assert custom_xml._testMethodDoc == "DOCS"


def test_CustomXmlResult_constructor(mocker):
    mock_xml_test_result = mocker.patch.object(
        xml_result.xmlrunner.runner._XMLTestResult, "__init__"
    )

    xml_result.XmlTestResult(
        "stream",
        "descriptions",
        "verbosity",
        "elapsed_times",
        "properties",
        "infoclass",
    )

    mock_xml_test_result.assert_called_once()
    # verify passed kwargs in the first and only call
    # assert_called_once_with doesn't fit here as it expects self as first argument
    assert mock_xml_test_result.call_args_list[0][1] == dict(
        stream="stream",
        descriptions="descriptions",
        verbosity="verbosity",
        elapsed_times="elapsed_times",
        properties="properties",
        infoclass="infoclass",
    )


def test_CustomXmlResult_constructor_ErrorHolder(mocker):
    mock_test_info = mocker.patch.object(
        xml_result.xmlrunner.result._TestInfo, "__init__"
    )
    test_method = unittest.suite._ErrorHolder("description")
    custom_xml = xml_result.TestInfo(
        "test_result",
        test_method,
        "outcome",
        "err",
        "subTest",
        "filename",
        "lineno",
        "doc",
    )

    mock_test_info.assert_called_once_with(
        "test_result",
        test_method,
        "outcome",
        "err",
        "subTest",
        "filename",
        "lineno",
        "doc",
    )
    assert custom_xml.test_ids == "{}"


def test_report_testcase(mocker):
    mocker.patch.object(xml_result.xmlrunner.runner._XMLTestResult, "__init__")
    mocker.patch.object(xml_result.XmlTestResult, "report_testcase")

    custom_xml_result = xml_result.XmlTestResult(
        "stream",
        "descriptions",
        "verbosity",
        "elapsed_times",
        "properties",
        "infoclass",
    )

    test_result = MockTestResult(test_ids='{"Component1": ["Req"]}')
    xml_testsuite = mocker.Mock()
    xml_document = mocker.Mock()

    custom_xml_result._report_testcase(test_result, xml_testsuite, xml_document)

    custom_xml_result.report_testcase.assert_called_once_with(
        test_result, xml_testsuite, xml_document
    )
    xml_testsuite.setAttribute.assert_called_once_with("test_ids", test_result.test_ids)
