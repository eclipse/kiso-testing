import concurrent.futures
import functools
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

from ..testrail.console import console
from ..testrail.containers import ResultContainer
from ..testrail.extraction import JunitReport, Status
from .api import XrayApi


def extract_test_results(results: str) -> list:
    """Extract each test result from the given xml reports.

    :param results: full path to the directory containing all Junit
        report

    :return: for each identified test cases the xray test id, and the it status, all the content
    """
    data = []
    test_path = "C:\\Users\\MOI4RT\\Documents\\workspace_ITF_projects\\Open_source\\kiso-testing\\"
    for file in os.listdir(test_path):
        if file.endswith(".xml"):
            with open(test_path + file) as xml:
                # logging.info(xml.read())
                data.append(xml.read())
            return data


def add_case_results(
    base_url: str,
    user: str,
    password: str,
    results: List[Tuple[int, Status]],
    test_execution_id: str | None = None,
) -> ResultContainer:
    """Upload all given results to xray.

    :param base_url: xray's base url
    :param user: user's session id
    :param password: user's password
    :param test_execution_id: xray's test ticket id
    :param results: test case ids to update and their results

    :return: all new test result information
    """
    responses = XrayApi.add_result_with_xml(
        base_url=base_url,
        user=user,
        password=password,
        test_execution_id=test_execution_id,
        data=results,
    )

    return responses
