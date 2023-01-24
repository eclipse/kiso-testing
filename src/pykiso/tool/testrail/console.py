##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


"""
Console printing
****************

:module: console

:synopsis: handle console fancy print

.. currentmodule:: console

"""

from rich.console import Console
from rich.table import Table

console = Console()


def print_projects(projects: list) -> None:
    """Print all available projects in a fancy way.

    :param projects: list of available project information (id, name and
        announcement)
    """
    table = Table(title="\n*** TestRail Project ***", show_lines=True)
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("NAME", style="yellow", justify="center")
    table.add_column("ANNOUNCEMENT", style="yellow", justify="center")

    for project in projects.iterate():
        table.add_row(str(project.id), str(project.name), str(project.announcement))

    console.print(table)


def print_suites(project_name: str, suites: list) -> None:
    """Print all available suites in a fancy way.

    :param project_name: associated project name
    :param suites: list of available suites information (id, name and
        description...)
    """
    table = Table(title=f"\n*** Project {project_name} suites ***", show_lines=True)
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("NAME", style="yellow", justify="center")
    table.add_column("DESCRIPTION", style="yellow", justify="center")
    table.add_column("IS_BASELINE", style="yellow", justify="center")
    table.add_column("IS_COMPLETED", style="yellow", justify="center")

    for suite in suites.iterate():
        table.add_row(
            str(suite.id),
            str(suite.name),
            str(suite.description),
            str(suite.is_baseline),
            str(suite.is_completed),
        )

    console.print(table)


def print_cases(project_name: str, cases: list) -> None:
    """Print all available cases in a fancy way.

    :param project_name: associated project name
    :param cases: list of available cases information
    """
    table = Table(
        title=f"\n*** Available cases for project {project_name} ***",
        show_lines=True,
    )
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("REQ ID", style="yellow", justify="center")
    table.add_column("TITLE", style="yellow", justify="center")

    for case in cases.iterate():
        table.add_row(
            str(case.id),
            str(case.custom_id),
            str(case.title),
        )

    console.print(table)


def print_runs(project_name: str, runs: list) -> None:
    """Print all available runs in a fancy way.

    :param project_name: associated project name
    :param runs: list of available runs information (id, title)
    """
    table = Table(
        title=f"\n*** Available runs for project {project_name} ***", show_lines=True
    )
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("NAME", style="yellow", justify="center")

    for run in runs.iterate():
        table.add_row(
            str(run.id),
            str(run.name),
        )

    console.print(table)


def print_milestones(project_name: str, milestones: list) -> None:
    """Print all available milestones in a fancy way.

    :param project_name: associated project name
    :param milestones: list of available milestones information (id, title)
    """
    table = Table(
        title=f"\n*** Available milestones for project {project_name} ***",
        show_lines=True,
    )
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("TITLE", style="yellow", justify="center")

    for mile in milestones.iterate():
        table.add_row(
            str(mile.id),
            str(mile.name),
        )

    console.print(table)


def print_results(run_name: str, results: list) -> None:
    """Print all available results in a fancy way.

    :param run_name: associated run name
    :param results: list of available result information (id, status_id)
    """
    table = Table(
        title=f"\n*** Uploaded results for run {run_name} ***",
        show_lines=True,
    )
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("TEST ID", style="yellow", justify="center")
    table.add_column("STATUS ID", style="yellow", justify="center")
    table.add_column("ELAPSED", style="yellow", justify="center")
    table.add_column("VERSION", style="yellow", justify="center")
    table.add_column("DEFECTS", style="yellow", justify="center")

    for result in results.iterate():
        table.add_row(
            str(result.id),
            str(result.test_id),
            str(result.status_id),
            str(result.elapsed),
            str(result.version),
            str(result.defects),
        )

    console.print(table)
