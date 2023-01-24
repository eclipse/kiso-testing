##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


"""
Report data extraction
**********************

:module: extraction

:synopsis: encapsulate all class used to extratc data from a specific
    fornmat, until now only Junit report is handle

.. currentmodule:: extraction
"""

import enum
import json
import xml
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as etree


class Status(enum.IntEnum):
    """All possible status on TestRail."""

    PASSED = 1
    TEST_EXECUTION_BLOCKED = 2
    UNTESTED = 3
    RETEST = 4
    MAJOR = 5
    NOT_IMPLEMENTED = 6
    CRITICAL = 7
    BLOCKER = 8
    MINOR = 9
    TRIVIAL = 11
    FAILED = 12


class JunitReport:
    """Concentrate all methods to extract specific data from Junit
    report."""

    #: test suite tag present in junit report
    TEST_SUITE_TAG: str = "testsuite"
    #: attribute from test suite tag to extract ids
    ID_PARAM_TAG: str = "test_ids"
    #: value from test_ids attribute seek for ids
    id_tag: str = "VTestId"

    @classmethod
    def set_id_tag(cls, tag: str) -> None:
        """Set the current xml attribute use to seek for requirement
        ids.

        :param tag: attribute to search for
        """
        cls.id_tag = tag

    @classmethod
    def search_for_xml(cls, folder: Path) -> List[Path]:
        """Return all junit report present in the given folder.

        :param result_folder: target folder containing all junit report

        :return: all found reports
        """
        return list(Path(folder).rglob("*.xml"))

    @classmethod
    def get_xml_root(cls, reports: List[Path]) -> List[xml.etree.ElementTree.Element]:
        """Parse all junit report contain in the given directory

        :param reports: full path to report directory

        :return: all parsed xml files
        """
        return [etree.parse(report).getroot() for report in reports]

    @classmethod
    def extract_suite_attrs(cls, root_elements: xml.etree.ElementTree.Element) -> dict:
        """Extract suite attributes.

        :param root_elements: parse xml file elements

        :return: test_ids xml attribute values
        """
        suite_attrs = []

        for root in root_elements:
            for suite_tag in root.iter(cls.TEST_SUITE_TAG):
                id_attr = suite_tag.attrib.get(cls.ID_PARAM_TAG)

                if id_attr is None:
                    continue

                if id_attr == "null":
                    continue

                suite_attrs.append(suite_tag.attrib)

        return suite_attrs

    @classmethod
    def extract_junit_results(cls, suite_attrs: List[dict]) -> List[tuple]:
        """Extract results for each extracted test case.

        :param suite_attrs: all found suite xml attributes

        :return: couple VTest Studio id/execution status
        """
        results = []

        for attrs in suite_attrs:
            ids = cls.get_ids(attrs)
            state = cls.get_case_status(attrs)
            if ids is not None:
                for _id in ids:
                    results.append((_id, state))

        return list(set(results))

    @classmethod
    def get_ids(cls, suite_attr: str) -> List[int]:
        """Retrieve all VTest Studio ids from the current suite xml
        attributes.

        :param suite_attrs: suite tag attributes

        :return: all found VTest Studio id otherwise None
        """
        id_attr = suite_attr.get(cls.ID_PARAM_TAG)

        ids = json.loads(id_attr).get(cls.id_tag)

        if ids is None:
            return

        return list(ids)

    @classmethod
    def get_case_status(cls, suite_attr: dict) -> int:
        """Determine the actual test execution status based on the suite
        result attributes.

        :param suite_attrs: suite tag attributes

        :return: actual test executi status (PASS, FAIL....)
        """
        is_skip = suite_attr["skipped"] != "0"
        is_fail = suite_attr["failures"] != "0"
        is_error = suite_attr["errors"] != "0"

        if is_skip:
            return Status.UNTESTED

        if is_fail or is_error:
            return Status.FAILED

        return Status.PASSED

    @classmethod
    def extract(cls, folder: Path):
        """Extract the VTest Sutdio ids and each test case execution
        status from all given Junit report.

        :param folder: full path to report directory

        :return: all found results and ids
        """
        reports = cls.search_for_xml(folder)
        root_elements = cls.get_xml_root(reports)
        suite_attrs = cls.extract_suite_attrs(root_elements)
        junit_resuts = cls.extract_junit_results(suite_attrs)

        return junit_resuts
