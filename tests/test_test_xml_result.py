##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

from collections import namedtuple

from pykiso.test_coordinator import test_xml_result

MockTestResult = namedtuple("TestMethod", "test_ids")


def test_TestInfo_custom_constructor(mocker):
    test_method = MockTestResult(test_ids={"Component1": ["Req"]})
    mock_test_info = mocker.patch.object(
        test_xml_result.xmlrunner.result._TestInfo, "__init__"
    )

    custom_xml = test_xml_result.TestInfo(
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


def test_CustomXmlResult_constructor(mocker):
    mock_test_result = mocker.patch.object(
        test_xml_result.xmlrunner.runner._XMLTestResult, "__init__"
    )

    test_xml_result.XmlTestResult(
        "stream",
        "descriptions",
        "verbosity",
        "elapsed_times",
        "properties",
        "infoclass",
    )

    mock_test_result.assert_called_once_with(
        stream="stream",
        descriptions="descriptions",
        verbosity="verbosity",
        elapsed_times="elapsed_times",
        properties="properties",
        infoclass="infoclass",
    )


def test_report_testcase(mocker):
    mocker.patch.object(test_xml_result.xmlrunner.runner._XMLTestResult, "__init__")
    mocker.patch.object(test_xml_result.XmlTestResult, "report_testcase")

    custom_xml_result = test_xml_result.XmlTestResult(
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
