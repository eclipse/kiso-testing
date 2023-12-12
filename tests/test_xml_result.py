##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import unittest
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import pykiso
from pykiso.test_result import xml_result


@pytest.fixture
def mock_log_options(mocker):
    return mocker.patch("pykiso.test_result.xml_result.get_logging_options")


@pytest.fixture
def mock_initialize_logging(mocker, mock_log_options):
    return mocker.patch("pykiso.test_result.xml_result.initialize_logging")


class MockTestResult:
    def __init__(self, test_ids=None, doc="") -> None:
        self.test_ids = test_ids
        self._testMethodDoc = doc
        self._test = MagicMock(properties=None)


def test_TestInfo_custom_constructor(mocker, mock_initialize_logging):
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


def test_CustomXmlResult_constructor_ErrorHolder(mocker, mock_initialize_logging):
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
    xml_testsuite.getElementsByTagName.return_value = []
    xml_document = mocker.Mock()

    custom_xml_result._report_testcase(test_result, xml_testsuite, xml_document)

    custom_xml_result.report_testcase.assert_called_once_with(
        test_result, xml_testsuite, xml_document
    )
    xml_testsuite.setAttribute.assert_called_once_with("test_ids", test_result.test_ids)


@pytest.fixture
def result_with_properties():
    mock_test_result = MockTestResult()
    mock_test_result._test.properties = {"dummy": "property", "will": "appear"}
    return mock_test_result


def test_report_testcase_with_properties(result_with_properties, mocker: MagicMock):
    mock_super_report_testcase = mocker.patch.object(
        xml_result.XmlTestResult, "report_testcase"
    )
    mock_report_testsuite_props = mocker.patch.object(
        xml_result.XmlTestResult, "_report_testsuite_properties"
    )

    mock_xml_testcase = mocker.MagicMock()
    # verify that the properties won't be written if there are already properties written
    mock_xml_testcase.getElementsByTagName.side_effect = [None, "some property"]

    mock_xml_testsuite = mocker.MagicMock()
    mock_xml_testsuite.getElementsByTagName.return_value = [
        mock_xml_testcase,
        mock_xml_testcase,
    ]

    mock_xml_document = mocker.MagicMock()

    xml_result.XmlTestResult._report_testcase(
        result_with_properties, mock_xml_testsuite, mock_xml_document
    )

    mock_super_report_testcase.assert_called_once_with(
        result_with_properties, mock_xml_testsuite, mock_xml_document
    )
    mock_xml_testsuite.getElementsByTagName.assert_called_once_with("testcase")
    mock_xml_testcase.getElementsByTagName.assert_called_with("properties")
    assert mock_xml_testcase.getElementsByTagName.call_count == 2

    mock_report_testsuite_props.assert_called_once_with(
        mock_xml_testcase, mock_xml_document, result_with_properties._test.properties
    )


def test_report_testcase_with_properties_invalid_type(
    result_with_properties, mocker: MagicMock
):
    mock_super_report_testcase = mocker.patch.object(
        xml_result.XmlTestResult, "report_testcase"
    )
    mock_report_testsuite_props = mocker.patch.object(
        xml_result.XmlTestResult, "_report_testsuite_properties"
    )

    mock_xml_testcase = mocker.MagicMock()
    mock_xml_testcase.getElementsByTagName.return_value = "won't be called"

    mock_xml_testsuite = mocker.MagicMock()
    mock_xml_testsuite.getElementsByTagName.return_value = [
        mock_xml_testcase,
        mock_xml_testcase,
    ]

    mock_xml_document = mocker.MagicMock()

    result_with_properties._test.properties = "INVALID TYPE"

    xml_result.XmlTestResult._report_testcase(
        result_with_properties, mock_xml_testsuite, mock_xml_document
    )

    mock_super_report_testcase.assert_called_once_with(
        result_with_properties, mock_xml_testsuite, mock_xml_document
    )
    mock_xml_testsuite.getElementsByTagName.assert_called_once_with("testcase")
    mock_xml_testcase.getElementsByTagName.assert_not_called()
    mock_report_testsuite_props.assert_not_called()
