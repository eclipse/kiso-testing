##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
test_xml_result
***************

:module: test_xml_result

:synopsis: overwrite xmlrunner.result to be able to add additional data into the xml report.

.. currentmodule:: test_xml_result

"""

import copy
import json
import sys
from io import TextIOWrapper
from xml.dom.minidom import Document, Element

import xmlrunner.result
import xmlrunner.runner


class TestInfo(xmlrunner.result._TestInfo):
    """This class keeps useful information about the execution of a test method.
    Used by XmlTestResult
    """

    def __init__(
        self,
        test_result: xmlrunner.runner._XMLTestResult,
        test_method,
        outcome: int = 0,
        err=None,
        subTest=None,
        filename: str = None,
        lineno: bool = None,
        doc: str = None,
    ):
        """Initialize the TestInfo class and append additional tag
           that have to be stored for each test

        :param test_result: test result class
        :param test_method: test method (dynamically created eg: test_case.MyTest2-1-2)
        :param outcome: result of the test (SUCCESS, FAILURE, ERROR, SKIP)
        :param err: error cached during test
        :param subTest: optional, refer the test id and the test description
        :param filename: name of the file
        :param lineno: store the test line number
        :param doc: additional documentation to store
        """
        super().__init__(
            test_result, test_method, outcome, err, subTest, filename, lineno, doc
        )

        # store extra tag
        self.test_ids = json.dumps(test_method.test_ids)


class XmlTestResult(xmlrunner.runner._XMLTestResult):
    """Test result class that can express test results in a XML report.
    Used by XMLTestRunner
    """

    def __init__(
        self,
        stream: TextIOWrapper = sys.stderr,
        descriptions: bool = True,
        verbosity: int = 1,
        elapsed_times: bool = True,
        properties=None,
        infoclass: xmlrunner.result._TestInfo = TestInfo,
    ):
        """Initialize the _XMLTestResult class.

        :param stream: buffered text interface to a buffered raw stream
        :param descriptions: include description of the test
        :param verbosity: print output into the console
        :param elapsed_times: include the time spend on the test
        :param properties: junit testsuite properties
        :param infoclass: class containing the test information
        """
        super().__init__(
            stream=stream,
            descriptions=descriptions,
            verbosity=verbosity,
            elapsed_times=elapsed_times,
            properties=properties,
            infoclass=infoclass,
        )

    # save the original method that will be overwritten
    report_testcase = copy.deepcopy(xmlrunner.runner._XMLTestResult._report_testcase)

    @staticmethod
    def _report_testcase(
        test_result: TestInfo, xml_testsuite: Element, xml_document: Document
    ):
        """Callback function that create the test case section into the XML document.

        :param test_result: result of a test run
        :param xml_testsuite: xml test suite to be written
        :param xml_document: xml document base
        """
        # call the original method
        XmlTestResult.report_testcase(test_result, xml_testsuite, xml_document)

        # here can be added additional tags that have to be stored into the xml test report
        xml_testsuite.setAttribute("test_ids", str(test_result.test_ids))

    # Catch and redefine xmlrunner.runner._XMLTestResult._report_testcase
    xmlrunner.runner._XMLTestResult._report_testcase = _report_testcase
