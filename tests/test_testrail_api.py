##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import pytest

from pykiso.tool.testrail.api import (
    HttpError,
    HttpRequest,
    TestRailApi,
    requests,
)

# prevent pytest from collecting these as test cases
TestRailApi.__test__ = False


class TestHttpRequest:
    @pytest.fixture(scope="class")
    def req_header(self):
        return {"Content-Type", "application/json"}

    @pytest.fixture(scope="class")
    def get_response(self):
        response = requests.Response()
        response.status_code = 200
        return response

    @pytest.fixture(scope="class")
    def post_response(self, get_response):
        return get_response

    def test_get(self, mocker, get_response, req_header):
        mock_get = mocker.patch.object(requests, "get", return_value=get_response)
        response = HttpRequest.get(url="https\\xyz.com", headers=req_header)

        mock_get.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "error",
        [
            requests.RequestException,
            requests.ConnectionError,
            requests.HTTPError,
            requests.URLRequired,
            requests.TooManyRedirects,
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.Timeout,
            requests.JSONDecodeError,
        ],
    )
    def test_get_exception(self, mocker, req_header, error):
        mocker.patch.object(requests, "get", side_effects=error)

        with pytest.raises(HttpError):
            HttpRequest.get(url="https\\xyz.com", headers=req_header)

    def test_post(self, mocker, post_response, req_header):
        mock_post = mocker.patch.object(requests, "post", return_value=post_response)
        response = HttpRequest.post(
            url="https\\xyz.com", headers=req_header, data=dict()
        )

        mock_post.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "error",
        [
            requests.RequestException,
            requests.ConnectionError,
            requests.HTTPError,
            requests.URLRequired,
            requests.TooManyRedirects,
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.Timeout,
            requests.JSONDecodeError,
        ],
    )
    def test_post_exception(self, mocker, req_header, error):
        mocker.patch.object(requests, "post", side_effects=error)

        with pytest.raises(HttpError):
            HttpRequest.post(url="https\\xyz.com", headers=req_header, data=dict())


class TestTestRailApi:
    def test_get_projects(self, mocker, projects_response):
        mock_get = mocker.patch.object(
            HttpRequest, "get", return_value=projects_response
        )

        projects = TestRailApi.get_projects(
            base_url="https\\xyz.com", user="xyz", password="secret"
        )

        mock_get.assert_called_once()
        assert projects["projects"][0]["id"] == 1
        assert projects["projects"][1]["id"] == 2

    def test_get_suites(self, mocker, suites_response):
        mock_get = mocker.patch.object(HttpRequest, "get", return_value=suites_response)

        suites = TestRailApi.get_suites(
            base_url="https\\xyz.com", user="xyz", password="secret", project_id=1
        )

        mock_get.assert_called_once()
        assert suites[0]["id"] == 1
        assert suites[1]["id"] == 2

    def test_get_cases(self, mocker, cases_response):
        mock_get = mocker.patch.object(HttpRequest, "get", return_value=cases_response)

        cases = TestRailApi.get_cases(
            base_url="https\\xyz.com",
            user="xyz",
            password="secret",
            project_id=1,
            suite_id=1,
        )

        mock_get.assert_called_once()
        assert cases["offset"] == 0
        assert cases["cases"][0]["id"] == 1
        assert cases["cases"][1]["id"] == 2

    def test_get_runs(self, mocker, runs_response):
        mock_get = mocker.patch.object(HttpRequest, "get", return_value=runs_response)

        runs = TestRailApi.get_runs(
            base_url="https\\xyz.com", user="xyz", password="secret", project_id=1
        )

        mock_get.assert_called_once()
        assert runs["offset"] == 0
        assert runs["runs"][0]["id"] == 1
        assert runs["runs"][1]["id"] == 2

    def test_get_milestones(self, mocker, milestones_response):
        mock_get = mocker.patch.object(
            HttpRequest, "get", return_value=milestones_response
        )

        milestones = TestRailApi.get_milestones(
            base_url="https\\xyz.com", user="xyz", password="secret", project_id=1
        )

        mock_get.assert_called_once()
        assert milestones["offset"] == 0
        assert milestones["milestones"][0]["id"] == 1
        assert milestones["milestones"][1]["id"] == 2

    def test_add_result_for_case(self, mocker, add_result_response):
        mock_post = mocker.patch.object(
            HttpRequest, "post", return_value=add_result_response
        )

        added_results = TestRailApi.add_result_for_case(
            base_url="https\\xyz.com",
            user="xyz",
            password="secret",
            run_id=1,
            case_id=1,
            data={},
        )

        mock_post.assert_called_once()
        assert added_results["id"] == 1

    def test_add_run(self, mocker, add_run_response):
        mock_post = mocker.patch.object(
            HttpRequest, "post", return_value=add_run_response
        )

        added_runs = TestRailApi.add_run(
            base_url="https\\xyz.com",
            user="xyz",
            password="secret",
            project_id=1,
            data={},
        )

        mock_post.assert_called_once()
        assert added_runs["failed_count"] == 10
        assert added_runs["milestone_id"] == 1

    def test_async_get_cases(self, mocker, cases_response):
        mock_get = mocker.patch.object(HttpRequest, "get", return_value=cases_response)

        cases = TestRailApi.async_get_cases(
            base_url="https\\xyz.com",
            user="xyz",
            password="secret",
            project_id=1,
            suite_ids=[1, 2, 3, 4, 5],
        )

        mock_get.assert_called()

        for case in cases:
            case["cases"][0] == 1

    def test_async_add_result_for_case(self, mocker, add_result_response):
        mock_post = mocker.patch.object(
            HttpRequest, "post", return_value=add_result_response
        )

        results = TestRailApi.async_add_result_for_case(
            base_url="https\\xyz.com",
            user="xyz",
            password="secret",
            run_id=1,
            case_ids=[1, 2, 3],
            data=[dict(), dict(), dict()],
        )

        mock_post.assert_called()

        for result in results:
            result["id"] == 1
