##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import unittest

import pytest

from pykiso.tool.show_tag import *


@pytest.fixture
def tmp_yaml_files(tmp_path: Path, request):
    """Create following file layout inside tmp_path
    tests
    |__ root_1.yaml
    |
    |__ root_2.yaml
    │
    │── suite_1
    │   │__ suite_1.yaml
    │
    └── suite_2
        |__ suite_2.yaml
        │
        └── suite_2_1
            │__ suite_2_1.yaml
    """
    root_only = request.param

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    root_1 = tests_dir / "root_1.yaml"
    root_1.write_text("text")
    root_2 = tests_dir / "root_2.yaml"
    root_2.write_text("text")

    yamls = [root_1, root_2]
    if root_only:
        return root_only, tests_dir, yamls

    suite_1_dir = tests_dir / "suite_1"
    suite_1_dir.mkdir()
    suite_1_yaml = suite_1_dir / "suite_1.yaml"
    suite_1_yaml.write_text("text")

    suite_2_dir = tests_dir / "suite_2"
    suite_2_dir.mkdir()
    suite_2_yaml = suite_2_dir / "suite_2.yaml"
    suite_2_yaml.write_text("text")

    suite_2_1_dir = tests_dir / "suite_2_1"
    suite_2_1_dir.mkdir()
    suite_2_1_yaml = suite_2_1_dir / "suite_2_1.yaml"
    suite_2_1_yaml.write_text("text")

    yamls.extend([suite_1_yaml, suite_2_yaml, suite_2_1_yaml])
    return root_only, tests_dir, yamls


@pytest.mark.parametrize("tmp_yaml_files", [(False,), (True,)], indirect=True)
def test_get_yaml_files(tmp_yaml_files):
    recurse, yaml_folder, expected_yaml_files = tmp_yaml_files
    yaml_files = get_yaml_files(yaml_folder, recurse)

    assert yaml_files == expected_yaml_files


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_show_tag(tmp_test):
    expected_config_name = "aux1_aux2.yaml"
    expected_number_of_tests = 5
    expected_test_names = (
        "test_aux1_aux2.SuiteSetup-1-0",
        "test_aux1_aux2.MyTest-1-1",
        "test_aux1_aux2.MyTest2-1-2",
        "test_aux1_aux2.MyTest3-1-3",
        "test_aux1_aux2.SuiteTearDown-1-0",
    )
    expected_tag_names = ("variant", "branch_level")
    expected_variant_values = ("variant1", "variant2")
    expected_branch_level_values = ("daily", "nightly")

    expected_table_headers = (
        "File name",
        "Number of tests",
        "Test cases",
    ) + expected_tag_names
    expected_table_data = [
        [
            expected_config_name,
            expected_number_of_tests,
            "\n".join(expected_test_names),
            "\n".join(expected_variant_values),
            "\n".join(expected_branch_level_values),
        ]
    ]

    sys.modules["pykiso.auxiliaries"] = mock.MagicMock()
    config_file = tmp_test
    cfg_dict = parse_config(config_file)
    test_cases = get_test_cases(cfg_dict)
    tags = get_test_tags(test_cases)
    single_config_result = build_result_dict(
        config_file.name, test_cases, tags, show_test_cases=True
    )
    all_results = [single_config_result]
    table_header, table_data = tabulate_test_information(all_results)

    assert table_header == list(expected_table_headers)
    assert table_data == list(expected_table_data)
