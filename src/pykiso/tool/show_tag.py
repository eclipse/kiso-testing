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

:synopsis: Passively load the test suites of YAML configuration files
    to show their test tags. Meant to be invoked as ``pykiso-tags``
    CLI utility.

.. currentmodule:: show_tag
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest import mock  # used to disable the test auxiliaries run

import click
from tabulate import tabulate

from pykiso.config_parser import parse_config
from pykiso.exceptions import TestCollectionError
from pykiso.test_coordinator import test_execution
from pykiso.test_coordinator.test_case import BasicTest
from pykiso.types import PathType


def get_yaml_files(config_path: PathType, recursive: bool) -> List[Path]:
    """List the YAML files passed to the CLI.

    :param config: YAML file or folder containing YAML files.
    :param recursive: boolean allowing to recurse all subfolders
        if a folder was provided.
    :raises FileNotFoundError: if a folder was provided but no
        YAML file was found.
    :raises ValueError: if a file was provided that does not have
        the .yaml extension.
    :return: list all all YAML file paths.
    """
    config = Path(config_path)
    pattern = "**/*.yaml" if recursive else "*.yaml"
    if config.is_dir():
        # search for all yaml files contained in it
        config_files = [
            config_file_path.resolve()
            for config_file_path in Path(config).glob(pattern)
        ]
        if not config_files:
            raise FileNotFoundError(f"No YAML configuration files found at {config}")
    else:
        if not config.suffix == ".yaml":
            raise ValueError("Provided file is not in YAML format")
        config_files = [config.resolve()]

    return config_files


def get_test_cases(cfg_dict: Dict[str, List[dict]]) -> List[BasicTest]:
    """Return the list of tests meant to be run by the provided
    test configuration file.

    :param cfg_dict: loaded configuration yaml file.
    :raises ValueError: if no test suite is specified in the
        configuration file.
    :return: list of tests meant to be run by the yaml file.
    """
    if "test_suite_list" not in cfg_dict:
        raise ValueError("Provided YAML file does not define a test suite")

    test_suites = test_execution.collect_test_suites(cfg_dict["test_suite_list"])
    test_cases = [tc for ts in test_suites if ts is not None for tc in ts._tests]
    return test_cases


def get_test_tags(test_case_list: List[BasicTest]) -> Dict[str, List[str]]:
    """Return the list of tag and values contained in the test case list

    :param test_case_list: list of loaded test cases.
    :return: dictionary linking the tag names to their values.
    """
    tag_dict = {}
    # search the tag for each test case
    for test_case in test_case_list:
        if test_case.tag is None:
            continue
        for tag_name, tag_values in test_case.tag.items():
            if tag_name not in tag_dict:
                tag_dict[tag_name] = list()
            # tag values are lists of strings
            tag_dict[tag_name].extend(tag_values)
            # remove duplicated tag values
            tag_dict[tag_name] = sorted(set(tag_dict[tag_name]))

    return tag_dict


def build_result_dict(
    config_file_name: str,
    test_case_list: List[BasicTest],
    test_tags: Dict[str, list],
    show_test_cases: bool = False,
) -> Dict[str, Union[str, int]]:
    """Build a dictionary containing the test information of a single
    configuration file.

    :param config_file_name: name of the configuration file.
    :param test_case_list: list of test cases meant to be loaded by
        pykiso with the provided configuration file.
    :param test_tags: dictionary containing the tags found in the
        provided configuration file's test suites.
    :param show_test_cases: set this flag to list all of the loaded
        test cases in the result dictionary (default is False).
    :return: the result
    """
    config_result_dict = {
        "File name": config_file_name,
        "Number of tests": len(test_case_list),
    }
    if show_test_cases:
        config_result_dict.update(
            {
                "Test cases": "\n".join(
                    f"{test.__module__}.{test.__class__.__qualname__}"
                    for test in test_case_list
                )
            }
        )
    if test_tags:
        tag_dict = {
            tag_name: "\n".join(tag_list) for tag_name, tag_list in test_tags.items()
        }
        config_result_dict = {**config_result_dict, **tag_dict}
    return config_result_dict


def tabulate_test_information(
    all_tests_info: List[Dict[str, Union[str, int]]], fill_char="-"
) -> Tuple[List[str], List[list]]:
    """Format a list of test information dictionaries to a tuple
    containing a table header and data in order to be tabulated.

    :param all_tests_info: list of test information corresponding
        to one loaded configuration file.
    :param fill_char: fill character for test suites that do not
        specify any tag, defaults to "-",
    :return: the formatted table header and table value as a tuple.
    """
    # get the entry with the most tags to use it as header for the table
    table_header = list(max(res.keys() for res in all_tests_info))
    table_rows = list()
    for test_info in all_tests_info:
        row = list()
        for idx, (corresponding_header, value) in enumerate(test_info.items()):
            # ensure that the current entry's tag corresponds to the header tags
            if idx == table_header.index(corresponding_header):
                row.append(value)
            else:
                row.append(fill_char)
        # fill the rest of the row values if no tag was found
        row.extend([fill_char] * (len(table_header) - len(row)))
        table_rows.append(row)
    return table_header, table_rows


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
@click.option(
    "--show-tests",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="""
    Extend the resulting table with all loaded test cases per configuration file.
    """,
)
def main(
    test_configuration: Tuple[PathType],
    output: Optional[PathType] = None,
    recurse_dir: bool = False,
    show_tests: bool = False,
):
    """Embedded Integration Test Framework - Test tag analysis.

    This tool loads all test cases from each test suite listed in
    the provided configuration file (in YAML format) in order to
    extract their tags.

    The result are shown as a table with the following format:

    \b
    ╒══════════════════════════════════════╤═══════════════════╤═══════════╤════════════════╕
    │ File name                            │   Number of tests │ variant   │ branch_level   │
    ╞══════════════════════════════════════╪═══════════════════╪═══════════╪════════════════╡
    │ my_config.yaml                       │                42 │ variant1  │ daily          │
    │                                      │                   │ variant3  │                │
    ├──────────────────────────────────────┼───────────────────┼───────────┼────────────────┤

    \f
    :param test_configuration_file: path to the YAML config file
        or folder containing configuration files.
    :param output: optional path to a file to dump the tag table.
        Supported formats are csv, json and txt.
    :param recurse_dir: if a folder is provided, recurse all
        subfolders to find configuration files (default: False).
    """
    # disable logging
    logging.getLogger().setLevel(logging.CRITICAL)
    # disable running the test auxiliaries when imported by the loader
    sys.modules["pykiso.auxiliaries"] = mock.MagicMock()

    all_results: List[Dict[str, Any]] = list()

    click.echo("\nStart analyzing provided configuration file...")
    # handle multiple files or folders provided by the user
    for config in test_configuration:
        # get all YAML files passed to the CLI
        yaml_files = get_yaml_files(config, recurse_dir)

        for config_file in yaml_files:
            try:
                # parse YAML configuration file (env vars, paths, etc.)
                cfg_dict = parse_config(config_file)
            except ValueError as e:
                click.echo(f"Failed to parse config file {config_file.name}: {e}")
                continue

            try:
                # get all test cases meant to be loaded by the config file
                test_cases = get_test_cases(cfg_dict)
            except ValueError as e:
                click.echo(
                    f"Failed to load test cases from config file {config_file.name}: {e.args[0]}"
                )
                continue
            except TestCollectionError as e:
                click.echo(
                    f"Failed to load test cases from config file {config_file.name}: {e}"
                )
                continue

            tags = get_test_tags(test_cases)

            single_config_result = build_result_dict(
                config_file.name, test_cases, tags, show_test_cases=show_tests
            )
            all_results.append(single_config_result)

    table_header, table_data = tabulate_test_information(all_results)
    table = tabulate(table_data, headers=table_header, tablefmt="fancy_grid")

    click.echo("\nAll valid configuration files have been processed successfully:")
    click.echo("\n{}\n".format(table))

    if output is None:
        return

    output = Path(output)

    with open(output, "w", encoding="utf-8") as f:
        if ".json" in output.suffixes:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        elif output.suffix == ".csv":
            csv.writer(output).writerows(table_header + table_data)
        elif output.suffix == ".txt":
            f.write(table)
        else:
            click.echo(f"Unsupported export format {output.suffix}")
            return

    click.echo(f"Test configuration dumped to '{output}'")
