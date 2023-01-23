##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


"""
TestRail API
************

:module: api

:synopsis: implement all the APIs used to interact with TestRail REST
    API

.. currentmodule:: api

"""

import base64
import concurrent.futures
import json
from enum import Enum
from typing import Callable, List

import requests


class ContentType(Enum):
    """Store all available header's content-type."""

    #: JSON content type
    JSON: str = "application/json"


class ApiVersion(Enum):
    """Store all available TestRail rest API version."""

    #: TestRail's V2 API
    V2: str = "index.php?/api/v2/"


class HttpError(Exception):
    """Raise if the status code from a HTTP request is different than
    200.
    """

    def __init__(self, status_code: str, reason: str) -> None:
        """Initialize error message attributes.

        :param status_code: response status code
        :param reason: response content
        """
        self.status_code = status_code
        self.reason = reason

    def __str__(self) -> str:
        """Exception message representation."""
        return f"HTTP request exit with status {self.status_code} : {self.reason}"


def handle_http_error(func: Callable) -> Callable:
    """Decorator used to handle HTTP request negative response

    :param func: inner handle function

    :return: the function returned value

    :raises Exception: if the response status code is different than
            200
    """

    def handle(*args: tuple, **kwargs: dict) -> requests.Response:
        """Handle sttaus code different than 200.

        :param args: positonnal arguments

        :return: kwargs named arguments

        :raises Exception: if the response status code is different than
                200
        """
        response = func(*args, **kwargs)

        if response.status_code != 200:
            raise HttpError(response.status_code, response.content)

        return response

    return handle


class HttpRequest:
    """Encapsulate all available HTTP requests."""

    @staticmethod
    @handle_http_error
    def get(url: str, headers: dict) -> requests.Response:
        """Send a GET HTTP request and return the received response.

        :param url: request target url
        :param headers: request's header (authorization, content-type)

        :return: received response from server

        :raises HttpError: if the response status code is different than
            200
        """
        return requests.get(url, headers=headers, verify=True)

    @staticmethod
    @handle_http_error
    def post(url: str, headers: dict, data: dict) -> requests.Response:
        """Send a POST HTTP request and return the received response.

        :param url: request target url
        :param headers: request's header
        :param data: request body

        :return: received response from server

        :raises HttpError: if the response status code is different than 200
        """
        return requests.post(url, headers=headers, data=data, verify=True)


class TestRailApi:
    """TestRail command API."""

    #: store the current API version in use
    API_VERSION: str = ApiVersion.V2.value

    @staticmethod
    def _construct_url(base_url: str, api_version: str, uri: str) -> str:
        """Construct the TestRail url.

        :param base_url: TestRail base url
        :param api_version: current api version in use
        :param uri: api command reference

        :return: request's url
        """
        return (
            f"{base_url}/{api_version}{uri}"
            if not base_url.endswith("/")
            else f"{base_url}{api_version}{uri}"
        )

    @staticmethod
    def _construct_header(user: str, password: str, content_type: str) -> dict:
        """Construct the request header by adding content and authorization
        part.

        :param user: user id
        :param password: user's password or API key
        :param content_type: reauest's content type (json,...)

        :return: request's fulfilled header
        """

        auth = str(
            base64.b64encode(bytes("%s:%s" % (user, password), "utf-8")), "ascii"
        ).strip()

        headers = {"Authorization": "Basic " + auth}
        headers["Content-Type"] = content_type
        return headers

    @classmethod
    def get_projects(cls, base_url: str, user: str, password: str) -> dict:
        """Retrieve all available projects under TestRail

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password or API key

        :return: all available projects information
        """
        url = cls._construct_url(base_url, cls.API_VERSION, uri="get_projects")
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.get(url=url, headers=headers)
        return json.loads(query_result.content)

    @classmethod
    def get_suites(
        cls, base_url: str, user: str, password: str, project_id: int
    ) -> dict:
        """Retrieve all available suite under the given project.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: project id in which to search for suites

        :return: all available suites information
        """
        url = cls._construct_url(
            base_url, cls.API_VERSION, uri=f"get_suites/{project_id}"
        )
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.get(url=url, headers=headers)
        return json.loads(query_result.content)

    @classmethod
    def get_cases(
        cls, base_url: str, user: str, password: str, project_id: int, suite_id: int
    ) -> dict:
        """Retrieve all available test cases under the given project and
        suite.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: targeted project id
        :param suite_id: targeted suite id

        :return: all available runs information
        """
        url = cls._construct_url(
            base_url, cls.API_VERSION, uri=f"get_cases/{project_id}&suite_id={suite_id}"
        )
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.get(url=url, headers=headers)
        return json.loads(query_result.content)

    @classmethod
    def async_get_cases(
        cls,
        base_url: str,
        user: str,
        password: str,
        project_id: int,
        suite_ids: List[int],
    ) -> List[dict]:
        """Asynchronously get test cases information.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: TestRail's project id
        :param suite_ids: all suite ids to search for test cases

        :return: all test case information
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(suite_ids)
        ) as executor:
            future_pools = [
                executor.submit(
                    TestRailApi.get_cases,
                    base_url,
                    user,
                    password,
                    project_id,
                    suite_id,
                )
                for suite_id in suite_ids
            ]
            return [
                pool.result()
                for pool in concurrent.futures.as_completed(future_pools, timeout=20)
            ]

    @classmethod
    def async_add_result_for_case(
        cls,
        base_url: str,
        user: str,
        password: str,
        run_id: int,
        case_ids: List[int],
        data: List[dict],
    ) -> List[dict]:
        """Asynchronously add results to all the given test cases.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param run_id: TestRail's run id
        :param case_id: all TestRail's case ids to update
        :param data: all case's results

        :return: all new test results
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(case_ids)
        ) as executor:
            future_pools = [
                executor.submit(
                    cls.add_result_for_case,
                    base_url,
                    user,
                    password,
                    run_id,
                    case_id,
                    _data,
                )
                for case_id, _data in zip(case_ids, data)
            ]
        return [
            pool.result()
            for pool in concurrent.futures.as_completed(future_pools, timeout=20)
        ]

    @classmethod
    def get_runs(cls, base_url: str, user: str, password: str, project_id: int) -> dict:
        """Retrieve all available runs under the given project.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: target project id

        :return: all available runs information
        """
        url = cls._construct_url(
            base_url, cls.API_VERSION, uri=f"get_runs/{project_id}"
        )
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.get(url=url, headers=headers)
        return json.loads(query_result.content)

    @classmethod
    def get_milestones(
        cls, base_url: str, user: str, password: str, project_id: int
    ) -> dict:
        """Retrieve all available milestones under the given project.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: target project id

        :return: all available milestones information
        """
        url = cls._construct_url(
            base_url, cls.API_VERSION, uri=f"get_milestones/{project_id}"
        )
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.get(url=url, headers=headers)
        return json.loads(query_result.content)

    @classmethod
    def add_result_for_case(
        cls,
        base_url: str,
        user: str,
        password: str,
        run_id: int,
        case_id: id,
        data: dict,
    ) -> dict:
        """Add the given result to the given test case for the
        corresponding run.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param run_id: TestRail's run id
        :param case_id: TestRail's case id
        :param data: result to add (status, report...)

        :return: new test result
        """
        url = cls._construct_url(
            base_url, cls.API_VERSION, uri=f"add_result_for_case/{run_id}/{case_id}"
        )
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.post(url=url, headers=headers, data=data)
        return json.loads(query_result.content)

    @classmethod
    def add_run(
        cls, base_url: str, user: str, password: str, project_id: int, data: dict
    ) -> dict:
        """Create a brand new TestRail run.

        :param base_url: TestRail's base url
        :param user: user's session id
        :param password: user's password
        :param project_id: TestRail's project id
        :param data: additional data to add to the run (milestonem,
            case ids,...)

        :return: the new test run
        """
        url = cls._construct_url(base_url, cls.API_VERSION, uri=f"add_run/{project_id}")
        headers = cls._construct_header(user, password, ContentType.JSON.value)
        query_result = HttpRequest.post(url=url, headers=headers, data=data)
        return json.loads(query_result.content)
