##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Test configuration analysis
***************************
:module: show_tag
:synopsis: Show the tag informations to the given tests
.. currentmodule:: show_tag
"""
import csv
import json
import logging
import sys
import unittest
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

import click
from tabulate import tabulate

from pykiso import __version__
from pykiso.config_parser import parse_config
from pykiso.global_config import Grabber
from pykiso.test_coordinator import test_execution
from pykiso.test_coordinator.test_case import BasicTest
from pykiso.test_coordinator.test_suite import flatten, tc_sort_key
from pykiso.types import PathType


def get_yaml_files(config: PathType) -> Tuple[Path, ...]:
    """List the YAML files passed to the CLI.

    :param config: YAML file or folder containing YAML files.
    :return: tuple of yaml Path
    """
    config = Path(config)
    if config.is_dir():
        # search for all yaml files contained in it
        config_files = tuple(
            config_file_path.resolve()
            for config_file_path in Path(config).glob("*.yaml")
        )
        if not config_files:
            raise FileNotFoundError(f"No YAML configuration files found at {config}")
    else:
        if not config.suffix == ".yaml":
            raise FileNotFoundError("Provided file is not in YAML format")
        config_files = (config.resolve(),)

    return config_files


def get_test_list(cfg_dict: Dict[str, List[dict]]) -> List[BasicTest]:
    """Return the list of tests impacted by the yaml

    :param cfg_dict: configuration dict of the yaml file
    :return: list of tests impacted by the yaml file
    """
    test_case_list = []

    # if the yaml file has a test suite list
    if "test_suite_list" not in cfg_dict:
        raise ValueError("Provided YAML file does not define a test suite")

    test_suites = test_execution.collect_test_suites(cfg_dict["test_suite_list"])
    test_cases = [tc for ts in test_suites for tc in ts._tests]
    return test_cases

    for test_suite_configuration in cfg_dict["test_suite_list"]:

        current_tc_list = []
        test_suite_path = test_suite_configuration["suite_dir"]
        click.echo(f"Loading test suite '{test_suite_path}'")

        # load tests from the specified folder
        loader = unittest.TestLoader()
        found_modules = loader.discover(
            test_suite_path,
            pattern=test_suite_configuration["test_filter_pattern"],
            top_level_dir=test_suite_path,
        )

        # sort the test case list by ascendant using test suite and test case id
        current_tc_list = sorted(flatten(found_modules), key=tc_sort_key)

        # get the test suite id if there is one
        test_suite_id = (
            test_suite_configuration["test_suite_id"]
            if "test_suite_id" in test_suite_configuration
            else None
        )

        # remove all tests who dont match the suite id
        if test_suite_id is not None:
            current_tc_list = [
                test_case
                for test_case in current_tc_list
                if not test_case.test_suite_id
                or test_suite_id == test_case.test_suite_id
            ]
        test_case_list += current_tc_list

    return test_case_list


def get_test_tags(test_case_list: List[BasicTest]) -> Dict[str, List[str]]:
    """Return the list of tag and values contained in the test case list

    :param test_case_list: list of loaded test cases.
    :return: dictionary linking the tag names to their value.
    """
    tag_dict = {}
    # search the tag for each test
    for test_case in test_case_list:
        if not test_case.tag:
            continue
        for tag_name, values in test_case.tag.items():
            # create a tuple if the tag doesnt exist yet
            if tag_name not in tag_dict:
                tag_dict[tag_name] = list()

            if isinstance(values, str):
                values = [values]

            tag_dict[tag_name].extend(values)
            # remove duplicated tag values
            tag_dict[tag_name] = sorted(set(tag_dict[tag_name]))

    return tag_dict


def tabulate_test_information(all_tests_info: List[Dict[str, Dict[str, Any]]]) -> str:
    table_header = list(max(res.keys() for res in all_tests_info))
    table_rows = list()
    for test_info in all_tests_info:
        row = list()
        for idx, (corresponding_header, value) in enumerate(test_info.items()):
            if idx == table_header.index(corresponding_header):
                row.append(value)
            else:
                row.append(None)
        table_rows.append(row)
    return tabulate(table_rows, table_header)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-c",
    "--test-configuration",
    required=True,
    type=click.Path(exists=True, dir_okay=True, readable=True),
    multiple=True,
    help="Path to the test configuration file (in YAML format) or folder containing test configuration files.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    help="Path to the exported test analysis file. Possible formats are csv, json or txt",
)
@click.option(
    "-r",
    "--recurse-dir",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="""
    If a folder is provided, set this flag to recurse all subfolders to find
    all configuration files (in YAML format).
    """,
)
@click.version_option(__version__)
@Grabber.grab_cli_config
def main(
    test_configuration: Tuple[PathType],
    output: Optional[PathType] = None,
    recurse_dir: bool = False,
):
    """Embedded Integration Test Framework - CLI Entry Point.
    \f
    :param test_configuration_file: path to the YAML config file
    :param log_path: path to directory or file to write logs to
    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :param report_type: if "test", the standard report, if "junit", a junit report is generated
    """
    # disable logging
    logging.getLogger().setLevel(100)
    # mock the auxiliaries
    sys.modules["pykiso.auxiliaries"] = mock.MagicMock()

    # init variables
    all_results: List[Dict[str, Any]] = list()

    click.echo("Start analyzing provided configuration file")
    # for each configuration given by the user
    for config in test_configuration:

        # get all yaml files
        yaml_files = get_yaml_files(config)

        for config_file in yaml_files:
            # click.echo(f"Parse configuration file {config_file}")
            # Get YAML configuration
            try:
                cfg_dict = parse_config(config_file)
            except ValueError as e:
                click.echo(f"Could not parse config file {config_file.name}: {e}")
                continue

            # Get all test cases loaded by the config file
            try:
                test_case_list = get_test_list(cfg_dict)
            except ValueError as e:
                click.echo(
                    f"Could get test list from config file {config_file.name}: {e}"
                )
                continue

            tags = get_test_tags(test_case_list)
            info_dict = {
                "File name": config_file.name,
                "Number of tests": len(test_case_list),
            }
            tag_dict = (
                {
                    tag_name: ", ".join(tag_list)
                    for tag_name, tag_list in tags.items()
                    if tags
                }
                if tags
                else {}
            )
            result = {**info_dict, **tag_dict}
            all_results.append(result)

    tabulated_results = tabulate_test_information(all_results)

    click.echo("\nAll valid configuration files have been processed successfully:")
    click.echo("\n{}\n".format(tabulated_results))

    if output is None:
        return

    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        click.echo(f"Test configuration dumped to '{output}'")
