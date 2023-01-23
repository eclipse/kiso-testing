##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
TestRail
********

:module: testrail

:synopsis: Just make the link between each features/services/API and
    encapsulate high level functions for an easy use

.. currentmodule:: testrail

"""
import concurrent.futures
import json
import sys
from typing import List, Tuple

from .api import TestRailApi
from .console import console
from .containers import (
    CaseContainer,
    CaseInfo,
    MilestoneContainer,
    MilestoneInfo,
    ProjectContainer,
    ProjectInfo,
    ResultContainer,
    ResultInfo,
    RunContainer,
    RunInfo,
    SuiteContainer,
    SuiteInfo,
)
from .extraction import JunitReport, Status


def extract_test_results(
    results: str, cases: CaseContainer
) -> List[Tuple[int, int, Status]]:
    """Extract each test case result from the given Junit reports.

    .. info:: based on the VTest Studio present in the Junit Report,
        this function will search for the linked TestRail's test case id
        and put a result in front of it.

    :param results: full path to the directory containing all Junit
        report
    :param cases: all available cases present on TestRail for the
        project


    :return: for each identified test cases the TestRail id,
        VTest Studio id, and the it status
    """

    case_results = []

    junit_results = JunitReport.extract(results)

    for custom_id, state in junit_results:
        rail_id = cases.find_id_equivalent(custom_id)
        if rail_id:
            case_results.append((rail_id, custom_id, state))

    return case_results


def create_projects_container(response: dict) -> ProjectContainer:
    """Create and populate the project container.

    :param response: received response from server

    :return: populated project container
    """
    container = ProjectContainer()

    for project in response["projects"]:
        container.add_project(
            ProjectInfo(project["id"], project["name"], project["announcement"])
        )

    return container


def create_suites_container(response: dict) -> SuiteContainer:
    """Create and populate the suite container.

    :param response: received response from server

    :return: populated suite container
    """
    container = SuiteContainer()

    for suite in response:
        container.add_suite(
            SuiteInfo(
                suite["id"],
                suite["name"],
                suite["description"],
                suite["is_baseline"],
                suite["is_completed"],
            )
        )

    return container


def create_result_container(response: List[dict]) -> ResultContainer:
    """Create and populate the result container.

    :param response: received response from server

    :return: populated result container
    """
    container = ResultContainer()

    for result in response:
        container.add_result(
            ResultInfo(
                result["id"],
                result["test_id"],
                result["status_id"],
                result["elapsed"],
                result["version"],
                result["defects"],
            )
        )

    return container


def create_cases_container(response: dict, custom_field: str) -> CaseContainer:
    """Create and populate the case container.

    :param response: received response from server

    :return: populated case container
    """
    container = CaseContainer()

    for case in response:
        container.add_case(CaseInfo(case["id"], case["title"], case.get(custom_field)))

    return container


def create_run_container(response: dict) -> RunContainer:
    """Create and populate the run container.

    :param response: received response from server

    :return: populated run container
    """
    container = RunContainer()

    for run in response["runs"]:
        container.add_run(RunInfo(run["id"], run["name"]))

    return container


def create_milestone_container(response: dict) -> MilestoneContainer:
    """Create and populate the milestone container.

    :param response: received response from server

    :return: populated milestone container
    """
    container = MilestoneContainer()

    for miles in response["milestones"]:
        container.add_milestone(MilestoneInfo(miles["id"], miles["name"]))

    return container


def search_for_project(
    base_url: str, user: str, password: str, project_name: str
) -> int:
    """Search for the project id in all available TestRail projects
    based on it name.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: TestRail's project name

    :return: associated project id
    """
    projects = enumerate_all_projects(base_url, user, password)

    project_id = projects.found_project_id_by_name(project_name)

    if project_id is None:
        console.print(
            f"Project named {project_name} doesn't exist!!!", style="bold red"
        )
        sys.exit(1)

    return project_id


def search_for_milestone(
    base_url: str, user: str, password: str, project_name: str, milestone_name: str
) -> int:
    """Search for the milestone id in all available TestRail milestones
    based on it name.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: TestRail's project name
    :param milestone_name: TestRail's milestone name

    :return: associated milestone id
    """
    _, milestones = enumerate_all_milestones(base_url, user, password, project_name)

    milestone_id = milestones.found_milestone_id_by_name(milestone_name)

    if milestone_id is None:
        console.print(
            f"Milestone named {milestone_name} doesn't exist!!!", style="bold red"
        )
        sys.exit(1)

    return milestone_id


def search_for_suite(
    base_url: str,
    user: str,
    password: str,
    project_name: str,
    suite_name: str,
) -> int:
    """Search for the suite id in all available TestRail suites
    based on it name.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: TestRail's project name
    :param suite_name: TestRail's suite name

    :return: associated suite id
    """
    _, suites = enumerate_all_suites(base_url, user, password, project_name)

    suite_id = suites.found_suite_id_by_name(suite_name)

    if suite_id is None:
        console.print(
            f"Milestone named {suite_name} doesn't exist!!!", style="bold red"
        )
        sys.exit(1)

    return suite_id


def enumerate_all_projects(base_url: str, user: str, password: str) -> ProjectContainer:
    """Retrieve all available project from testRail.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password

    :return: all project information encapsulated in a class container
    """
    response = TestRailApi.get_projects(base_url=base_url, user=user, password=password)
    return create_projects_container(response)


def enumerate_all_suites(
    base_url: str, user: str, password: str, project_name: str
) -> Tuple[int, SuiteContainer]:
    """Retrieve all available suites from the given project.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: full project name under Testrail

    :return: all suite information encapsulated in a class container
    """
    project_id = search_for_project(base_url, user, password, project_name)

    response = TestRailApi.get_suites(
        base_url=base_url, user=user, password=password, project_id=project_id
    )
    suites = create_suites_container(response)
    return project_id, suites


def enumerate_all_cases(
    base_url: str, user: str, password: str, project_name: str, custom_field: str
) -> Tuple[int, CaseContainer]:
    """Retrieve all available cases from the given project and all the
    available suites..

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: full project name under Testrail

    :return: all case information encapsulated in a class container
    """
    responses = list()

    project_id, suites = enumerate_all_suites(base_url, user, password, project_name)
    suite_ids = [suite.id for suite in suites.iterate()]

    try:
        responses = TestRailApi.async_get_cases(
            base_url, user, password, project_id, suite_ids
        )
    except concurrent.futures.TimeoutError:
        console.print("Request timeout reach!!!", style="bold red")
        sys.exit(1)

    flat_resp = [case for resp in responses for case in resp["cases"]]

    cases = create_cases_container(flat_resp, custom_field)
    return project_id, cases


def enumerate_all_runs(
    base_url: str, user: str, password: str, project_name: str
) -> Tuple[int, RunContainer]:
    """Retrieve all available runs from the given project.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: full project name under Testrail

    :return: all run information encapsulated in a class container
    """
    project_id = search_for_project(base_url, user, password, project_name)

    response = TestRailApi.get_runs(
        base_url=base_url, user=user, password=password, project_id=project_id
    )

    runs = create_run_container(response)
    return project_id, runs


def enumerate_all_milestones(
    base_url: str, user: str, password: str, project_name: str
) -> Tuple[int, MilestoneContainer]:
    """Retrieve all available milestones from the given project.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_name: full project name under Testrail

    :return: all milestone information encapsulated in a class container
    """
    project_id = search_for_project(base_url, user, password, project_name)

    response = TestRailApi.get_milestones(
        base_url=base_url, user=user, password=password, project_id=project_id
    )

    runs = create_milestone_container(response)
    return project_id, runs


def add_case_results(
    base_url: str,
    user: str,
    password: str,
    run_id: int,
    results: List[Tuple[int, int, Status]],
) -> ResultContainer:
    """Upload all given results to TestRail.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param run_id: TestRail's run id
    :param results: test case ids to update and their results

    :return: all new test result information
    """
    responses = []
    data_list = []
    case_list = []

    for rail_ids, _, status in results:
        body = {"status_id": status.value}
        data = bytes(json.dumps(body), "utf-8")
        for rail_id in rail_ids:
            data_list.append(data)
            case_list.append(rail_id)

    try:
        responses = TestRailApi.async_add_result_for_case(
            base_url,
            user,
            password,
            run_id,
            case_list,
            data_list,
        )
    except concurrent.futures.TimeoutError:
        console.print("Request timeout reach!!!", style="bold red")
        sys.exit(1)

    results = create_result_container(responses)
    return results


def create_new_run(
    base_url: str,
    user: str,
    password: str,
    project_id: int,
    run_name: str,
    suite_id: int,
    milestone_id: str,
    case_ids: List[int],
) -> int:
    """Add a test run to Testrail.

    :param base_url: TestRail's base url
    :param user: user's session id
    :param password: user's password
    :param project_id: TestRail's project id
    :param suite_id: TestRail's suite id
    :param milestone: TestRail's milestone id
    :param case_ids: test case ids to associate with this new run

    :return: created run id
    """
    body = {
        "suite_id": suite_id,
        "name": run_name,
        "milestone_id": milestone_id,
        "include_all": False,
        "case_ids": case_ids,
    }
    data = bytes(json.dumps(body), "utf-8")

    response = TestRailApi.add_run(
        base_url=base_url,
        user=user,
        password=password,
        project_id=project_id,
        data=data,
    )

    return response["id"]
