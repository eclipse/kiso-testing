##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Containers
**********

:module: containers

:synopsis: encapsulate all class containers use to store TestRail
    information retrieve using REST API

.. currentmodule:: containers

"""
from dataclasses import dataclass, field
from typing import Generator, List, Optional


@dataclass(frozen=True)
class ProjectInfo:
    """Store TestRail project information."""

    #: project id under TestRail
    id: int
    #: project name under TestRail
    name: str
    #: project description
    announcement: str

    def __str__(self) -> str:
        """Project info representation."""
        return f"{self.id}:{self.name}:{self.announcement}"


@dataclass
class ProjectContainer:
    """Simply contain all collected project information."""

    #: store all project information
    projects: List[ProjectInfo] = field(default_factory=list)

    def add_project(self, project: ProjectInfo) -> None:
        """Add project information to the project container.

        :param project: project information to add
        """
        self.projects.append(project)

    def found_project_id_by_name(self, project_name: str) -> Optional[int]:
        """Found project id based on his name.

        :param project_name: project name

        :return: first founded project id otherwise None
        """
        ids = [project.id for project in self.iterate() if project.name == project_name]

        if ids:
            return ids.pop()
        return None

    def iterate(self) -> Generator[ProjectInfo, None, None]:
        """Yield all projects contained in the container.

        :return: project information
        """
        for project in self.projects:
            yield project


@dataclass(frozen=True)
class SuiteInfo:
    """Store TestRail suite information."""

    #: suite id under TestRail
    id: int
    #: suite name under TestRail
    name: str
    #: suite description
    description: str
    #: indicate if it's under a baseline
    is_baseline: bool
    #: indicate if this suite is completed
    is_completed: bool

    def __str__(self) -> str:
        """Suite info representation."""
        return f"{self.id}:{self.name}:{self.description}"


@dataclass
class SuiteContainer:
    """Simply contain all collected suite information."""

    #: store all suite information
    suites: List[SuiteInfo] = field(default_factory=list)

    def add_suite(self, suite: ProjectInfo) -> None:
        """Add suite information to the suite container.

        :param suite: suite information to add
        """
        self.suites.append(suite)

    def found_suite_id_by_name(self, suite_name: str) -> Optional[int]:
        """Found suite id based on his name.

        :param suite_name: suite name

        :return: first founded suite id otherwise None
        """
        ids = [suite.id for suite in self.iterate() if suite.name == suite_name]

        if ids:
            return ids.pop()
        return None

    def iterate(self) -> Generator[SuiteInfo, None, None]:
        """Yield all suites contained in the container.

        :return: suite information
        """
        for suite in self.suites:
            yield suite


@dataclass(frozen=True)
class CaseInfo:
    """Store TestRail case information."""

    #: case id under TestRail
    id: int
    #: case title under TestRail
    title: str
    #: requirement id
    custom_id: str

    def __str__(self) -> str:
        """Case info representation."""
        return f"{self.id}:{self.title}:{self.custom_id}"


@dataclass
class CaseContainer:
    """Simply contain all collected case information."""

    #: store all case information
    cases: List[SuiteInfo] = field(default_factory=list)

    def add_case(self, case: CaseInfo) -> None:
        """Add case information to the case container.

        :param case: case information to add
        """
        self.cases.append(case)

    def find_id_equivalent(self, custom_ids: List[str]) -> List[int]:
        """return the equivalent TestRail case ids based on the given
        custom id.

        :param custom_ids: custom case ids

        :return: all related TestRail case ids
        """
        return [
            case.id
            for case in self.iterate()
            if case.custom_id is not None and case.custom_id in custom_ids
        ]

    def iterate(self) -> Generator[CaseInfo, None, None]:
        """Yield all cases contained in the container.

        :return: case information
        """
        for case in self.cases:
            yield case


@dataclass(frozen=True)
class RunInfo:
    """Store TestRail run information."""

    #: run id under TestRail
    id: int
    #: run name under TestRail
    name: str

    def __str__(self) -> str:
        """Suite info representation."""
        return f"{self.id}:{self.name}"


@dataclass
class RunContainer:
    """Simply contain all collected case information."""

    #: store all runs information
    runs: List[RunInfo] = field(default_factory=list)

    def add_run(self, run: RunInfo) -> None:
        """Add run information to the run container.

        :param run: run information to add
        """
        self.runs.append(run)

    def iterate(self) -> Generator[RunInfo, None, None]:
        """Yield all runs contained in the container.

        :return: run information
        """
        for run in self.runs:
            yield run


@dataclass(frozen=True)
class MilestoneInfo:
    """Store TestRail milestone information."""

    #: milestone id under TestRail
    id: int
    #: milestone title under TestRail
    name: str

    def __str__(self) -> str:
        """Case info representation."""
        return f"{self.id}:{self.name}"


@dataclass
class MilestoneContainer:
    """Simply contain all collected milestone information."""

    #: store all milestone information
    milestones: List[MilestoneInfo] = field(default_factory=list)

    def add_milestone(self, milestone: MilestoneInfo) -> None:
        """Add milestone information to the milestone container.

        :param milestone: milestone information to add
        """
        self.milestones.append(milestone)

    def found_milestone_id_by_name(self, milestone_name: str) -> Optional[int]:
        """Found milestone id based on his name.

        :param milestone_name: milestone name

        :return: first founded milestone id otherwise None
        """
        ids = [
            milestone.id
            for milestone in self.iterate()
            if milestone.name == milestone_name
        ]

        if ids:
            return ids.pop()
        return None

    def iterate(self) -> Generator[MilestoneInfo, None, None]:
        """Yield all milestones contained in the container.

        :return: milestone information
        """
        for milestone in self.milestones:
            yield milestone


@dataclass(frozen=True)
class ResultInfo:
    """Store TestRail result information."""

    #: the unique ID of the test result
    id: int
    #: the ID of the test this test result belongs to
    test_id: int
    #: the status of the test result
    status_id: str
    #: the amount of time it took to execute the test
    elapsed: str
    #: the (build) version of the test was executed against
    version: str
    #: A comma-separated list of defects linked to the test result
    defects: str

    def __str__(self) -> str:
        """Result info representation."""
        return f"{self.id}:{self.test_id}: status {self.status_id} : version {self.version}"


@dataclass
class ResultContainer:
    """Simply contain all collected result information."""

    #: store all result information
    results: List[ResultInfo] = field(default_factory=list)

    def add_result(self, result: ResultInfo) -> None:
        """Add result information to the result container.

        :param result: result information to add
        """
        self.results.append(result)

    def iterate(self) -> Generator[ResultInfo, None, None]:
        """Yield all results contained in the container.

        :return: result information
        """
        for result in self.results:
            yield result
