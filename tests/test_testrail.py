##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################
import concurrent.futures
import json

import pytest

from pykiso.tool.testrail import testrail
from pykiso.tool.testrail.testrail import (
    CaseContainer,
    CaseInfo,
    JunitReport,
    MilestoneContainer,
    MilestoneInfo,
    ProjectContainer,
    ProjectInfo,
    ResultContainer,
    RunContainer,
    Status,
    SuiteContainer,
    SuiteInfo,
    TestRailApi,
    add_case_results,
    create_cases_container,
    create_milestone_container,
    create_new_run,
    create_projects_container,
    create_result_container,
    create_run_container,
    create_suites_container,
    enumerate_all_cases,
    enumerate_all_milestones,
    enumerate_all_projects,
    enumerate_all_runs,
    enumerate_all_suites,
    extract_test_results,
    search_for_milestone,
    search_for_project,
    search_for_suite,
    sys,
)


def test_extract_test_results(mocker):
    container = CaseContainer()
    container.add_case(CaseInfo(1, "super title", "123"))
    mocker.patch.object(JunitReport, "extract", return_value=[(["123"], Status.PASSED)])

    results = extract_test_results([], container)

    rail_id, custom_id, state = results.pop()

    assert rail_id == [1]
    assert custom_id == ["123"]
    assert state == Status.PASSED


def test_extract_test_results_no_matching(mocker):
    container = CaseContainer()
    container.add_case(CaseInfo(1, "super title", "456"))
    mocker.patch.object(JunitReport, "extract", return_value=[(["123"], Status.PASSED)])

    results = extract_test_results([], container)

    assert results == []


def test_create_projects_container(projects_response):
    container = create_projects_container(json.loads(projects_response.content))

    assert isinstance(container, ProjectContainer)
    assert container.projects[0].id == 1
    assert container.projects[1].id == 2


def test_create_suites_containerr(suites_response):
    container = create_suites_container(json.loads(suites_response.content))

    assert isinstance(container, SuiteContainer)
    assert container.suites[0].id == 1
    assert container.suites[1].id == 2


def test_create_result_container(add_result_response):
    results = json.loads(add_result_response.content)
    container = create_result_container([results] * 3)

    assert isinstance(container, ResultContainer)
    assert container.results[0].id == 1


def test_create_cases_container(cases_response):
    cases = json.loads(cases_response.content)["cases"]
    container = create_cases_container(cases, custom_field="custom_field_id")

    assert isinstance(container, CaseContainer)
    assert container.cases[0].id == 1


def test_create_run_container(runs_response):
    container = create_run_container(json.loads(runs_response.content))

    assert isinstance(container, RunContainer)
    assert container.runs[0].id == 1
    assert container.runs[1].id == 2


def test_create_milestone_container(milestones_response):
    container = create_milestone_container(json.loads(milestones_response.content))

    assert isinstance(container, MilestoneContainer)
    assert container.milestones[0].id == 1


def test_search_for_project(mocker):
    container = ProjectContainer()
    container.add_project(ProjectInfo(1, "super_project", ""))
    mocker.patch.object(testrail, "enumerate_all_projects", return_value=container)

    project_id = search_for_project(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
    )

    assert project_id == 1


def test_search_for_project_not_maching(mocker):
    mock_exit = mocker.patch.object(sys, "exit")
    container = ProjectContainer()
    container.add_project(ProjectInfo(1, "super_project", ""))
    mocker.patch.object(testrail, "enumerate_all_projects", return_value=container)

    project_id = search_for_project(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="error_project",
    )

    mock_exit.assert_called_with(1)


def test_search_for_milestone(mocker):
    container = MilestoneContainer()
    container.add_milestone(MilestoneInfo(1, "huge_milestone"))
    mocker.patch.object(
        testrail, "enumerate_all_milestones", return_value=(1, container)
    )

    milestone_id = search_for_milestone(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
        milestone_name="huge_milestone",
    )

    assert milestone_id == 1


def test_search_for_project_not_maching(mocker):
    mock_exit = mocker.patch.object(sys, "exit")
    container = MilestoneContainer()
    container.add_milestone(MilestoneInfo(1, "huge_milestone"))
    mocker.patch.object(
        testrail, "enumerate_all_milestones", return_value=(1, container)
    )

    project_id = search_for_milestone(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="error_project",
        milestone_name="error_milestone",
    )

    mock_exit.assert_called_with(1)


def test_search_for_suite(mocker):
    container = SuiteContainer()
    container.add_suite(SuiteInfo(1, "huge_suite", "", True, False))
    mocker.patch.object(testrail, "enumerate_all_suites", return_value=(1, container))

    suite_id = search_for_suite(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
        suite_name="huge_suite",
    )

    assert suite_id == 1


def test_search_for_suite(mocker):
    mock_exit = mocker.patch.object(sys, "exit")
    container = SuiteContainer()
    container.add_suite(SuiteInfo(1, "huge_suite", "", True, False))
    mocker.patch.object(testrail, "enumerate_all_suites", return_value=(1, container))

    suite_id = search_for_suite(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
        suite_name="error_suite",
    )

    mock_exit.assert_called_with(1)


def test_enumerate_all_projects(mocker, projects_response):

    mocker.patch.object(
        TestRailApi, "get_projects", return_value=json.loads(projects_response.content)
    )

    container = enumerate_all_projects(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
    )

    assert container.projects[0].id == 1
    assert container.projects[1].id == 2


def test_enumerate_all_suites(mocker, suites_response):
    mocker.patch.object(testrail, "search_for_project", return_value=1)
    mocker.patch.object(
        TestRailApi, "get_suites", return_value=json.loads(suites_response.content)
    )

    project_id, container = enumerate_all_suites(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
    )

    assert project_id == 1
    assert isinstance(container, SuiteContainer)
    assert container.suites[0].id == 1
    assert container.suites[1].id == 2


def test_enumerate_all_cases(mocker, cases_response):
    container = SuiteContainer()
    container.add_suite(SuiteInfo(1, "huge_suite", "", True, False))
    mocker.patch.object(testrail, "enumerate_all_suites", return_value=(1, container))
    mocker.patch.object(
        TestRailApi,
        "async_get_cases",
        return_value=[json.loads(cases_response.content)] * 5,
    )

    project_id, container = enumerate_all_cases(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
        custom_field="custom_field_id",
    )

    assert project_id == 1
    assert isinstance(container, CaseContainer)
    assert container.cases[0].id == 1
    assert container.cases[0].custom_id == 1234


def test_enumerate_all_cases_timeout(mocker):
    mock_exit = mocker.patch.object(sys, "exit")
    container = SuiteContainer()
    container.add_suite(SuiteInfo(1, "huge_suite", "", True, False))
    mocker.patch.object(testrail, "enumerate_all_suites", return_value=(1, container))
    mocker.patch.object(
        TestRailApi, "async_get_cases", side_effect=concurrent.futures.TimeoutError
    )

    enumerate_all_cases(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
        custom_field="custom_field_id",
    )

    mock_exit.assert_called_with(1)


def test_enumerate_all_runs(mocker, runs_response):
    mocker.patch.object(testrail, "search_for_project", return_value=1)
    mocker.patch.object(
        TestRailApi, "get_runs", return_value=json.loads(runs_response.content)
    )

    project_id, container = enumerate_all_runs(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
    )

    assert project_id == 1
    assert isinstance(container, RunContainer)
    assert container.runs[0].id == 1
    assert container.runs[1].id == 2


def test_enumerate_all_milestones(mocker, milestones_response):
    mocker.patch.object(testrail, "search_for_project", return_value=1)
    mocker.patch.object(
        TestRailApi,
        "get_milestones",
        return_value=json.loads(milestones_response.content),
    )

    project_id, container = enumerate_all_milestones(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_name="super_project",
    )

    assert project_id == 1
    assert isinstance(container, MilestoneContainer)
    assert container.milestones[0].id == 1
    assert container.milestones[1].id == 2


def test_add_case_results(mocker, add_result_response):
    results = [([1], 1, Status.PASSED)]
    mocker.patch.object(
        TestRailApi,
        "async_add_result_for_case",
        return_value=[json.loads(add_result_response.content)] * 5,
    )

    container = add_case_results(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        run_id=1,
        results=results,
    )

    assert container.results[0].id == 1
    assert isinstance(container, ResultContainer)


def test_add_case_results_timeout(mocker):
    mock_exit = mocker.patch.object(sys, "exit")
    results = [([1], 1, Status.PASSED)]
    mocker.patch.object(
        TestRailApi,
        "async_add_result_for_case",
        side_effect=concurrent.futures.TimeoutError,
    )

    add_case_results(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        run_id=1,
        results=results,
    )

    mock_exit.assert_called_with(1)


def test_create_run(mocker, add_run_response):
    mocker.patch.object(
        TestRailApi, "add_run", return_value=json.loads(add_run_response.content)
    )

    run_id = create_new_run(
        base_url="https\\xyz.com",
        user="xyz",
        password="secret",
        project_id=1,
        run_name="super_run",
        suite_id=1,
        milestone_id=1,
        case_ids=[1, 2, 3, 4],
    )

    assert run_id == 1
