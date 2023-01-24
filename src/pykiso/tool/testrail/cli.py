##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


"""
TestRail tool command line interface
************************************

:module: cli

:synopsis: CLI entry-point for TestRail helper tool

.. currentmodule:: cli

"""
import getpass

import click

from .console import (
    print_cases,
    print_milestones,
    print_projects,
    print_results,
    print_runs,
    print_suites,
)
from .extraction import JunitReport
from .testrail import (
    add_case_results,
    create_new_run,
    enumerate_all_cases,
    enumerate_all_milestones,
    enumerate_all_projects,
    enumerate_all_runs,
    enumerate_all_suites,
    extract_test_results,
    search_for_milestone,
    search_for_suite,
)


@click.group()
@click.option(
    "--user",
    help="TestRail user id",
    required=True,
    default=None,
    hide_input=True,
)
@click.option(
    "--password",
    help="Valid TestRail API key (if not given ask at command prompt level)",
    required=False,
    default=None,
    hide_input=True,
)
@click.option(
    "--url",
    help="URL of TestRail server",
    required=True,
)
@click.pass_context
def cli_testrail(ctx: dict, user: str, password: str, url: str) -> None:
    """TestRail interaction tool."""
    ctx.ensure_object(dict)
    ctx.obj["USER"] = user or input("Enter Client ID TestRail and Press enter:")
    ctx.obj["PASSWORD"] = password or getpass.getpass(
        "Enter your password and Press ENTER:"
    )
    ctx.obj["URL"] = url


@cli_testrail.command("projects")
@click.pass_context
def cli_projects(ctx) -> None:
    """Returns the list of available projects."""
    projects = enumerate_all_projects(
        base_url=ctx.obj["URL"], user=ctx.obj["USER"], password=ctx.obj["PASSWORD"]
    )
    print_projects(projects)


@cli_testrail.command("suites")
@click.option(
    "-p",
    "--project",
    help="TestRail Project's name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.pass_context
def cli_suites(ctx, project: str) -> None:
    """Returns a list of all the test suites contained in a given project."""
    _, suites = enumerate_all_suites(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
    )
    print_suites(project, suites)


@cli_testrail.command("cases")
@click.option(
    "-p",
    "--project",
    help="TestRail Project's name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.option(
    "--custom-field",
    help="TestRail's case custom field use to store the requirement id",
    required=False,
    default="id",
    type=click.STRING,
)
@click.pass_context
def cli_cases(
    ctx,
    project: str,
    custom_field: str,
) -> None:
    """Returns a list of all cases contained in a project."""
    _, cases = enumerate_all_cases(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
        custom_field=custom_field,
    )
    print_cases(project, cases)


@cli_testrail.command("runs")
@click.option(
    "-p",
    "--project",
    help="TestRail's project name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.pass_context
def cli_runs(ctx, project: str) -> None:
    """Returns a list of all runs contained in a project."""
    _, runs = enumerate_all_runs(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
    )
    print_runs(project, runs)


@cli_testrail.command("milestones")
@click.option(
    "-p",
    "--project",
    help="TestRail's project name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.pass_context
def cli_milestones(ctx, project: str) -> None:
    """Returns the list of all milestones contained in a project."""
    _, milestones = enumerate_all_milestones(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
    )
    print_milestones(project, milestones)


@cli_testrail.command("upload")
@click.option(
    "-n",
    "--run-name",
    help="How to name the created run on TestRail",
    required=True,
    default=None,
    type=click.STRING,
)
@click.option(
    "-p",
    "--project",
    help="TestRail's project name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.option(
    "-s",
    "--suite",
    help="TestRail's suite name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.option(
    "-m",
    "--milestone",
    help="TestRail's milestone name",
    required=True,
    default=None,
    type=click.STRING,
)
@click.option(
    "-r",
    "--results",
    help="full path to the folder containing the JUNIT reports",
    type=click.Path(exists=True, resolve_path=True),
    required=True,
)
@click.option(
    "--tag",
    help="attribute in JUNIT report use to store requirements ids",
    required=False,
    default="VTestId",
    type=click.STRING,
)
@click.option(
    "--custom-field",
    help="TestRail's case custom field use to store the requirement id",
    required=False,
    default="custom_vteststudio_id",
    type=click.STRING,
)
@click.pass_context
def cli_upload(
    ctx,
    run_name: str,
    project: str,
    suite: str,
    milestone: str,
    results: str,
    attr: str,
    custom_field: str,
) -> None:
    """Upload all test case results on TestRail."""
    JunitReport.set_id_tag(attr)

    # get all available cases from the given project
    project_id, cases = enumerate_all_cases(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
        custom_field=custom_field,
    )
    # get the milestone id from the given milestone name for the run
    # creation
    milestone_id = search_for_milestone(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
        milestone_name=milestone,
    )
    # get the suite id from the given suite name for the run creation
    suite_id = search_for_suite(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_name=project,
        suite_name=suite,
    )
    # extract the ids from each given JUNIT report and finally get the
    # couple (TestRail id, req id, state)
    case_results = extract_test_results(results=results, cases=cases)
    case_ids = [rail_id for rail_ids, _, _ in case_results for rail_id in rail_ids]
    # Create a brand new run on TestRail and associate the case ids
    run_id = create_new_run(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        project_id=project_id,
        run_name=run_name,
        suite_id=suite_id,
        milestone_id=milestone_id,
        case_ids=case_ids,
    )
    # update the new created run with case statuses
    test_results = add_case_results(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        run_id=run_id,
        results=case_results,
    )
    print_results(run_name, test_results)
