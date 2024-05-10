##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


from unittest.mock import PropertyMock

import pytest
from click.testing import CliRunner

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


@pytest.fixture
def basic_test_mock(mocker):
    return mocker.patch("pykiso.tool.show_tag.BasicTest")


@pytest.fixture(autouse=True, scope="module")
def aux_mock():
    sys.modules["pykiso.auxiliaries"] = mock.MagicMock()


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize("tmp_yaml_files", [(False,), (True,)], indirect=True)
def test_get_yaml_files(tmp_yaml_files):
    recurse, yaml_folder, expected_yaml_files = tmp_yaml_files

    yaml_files = get_yaml_files(yaml_folder, recurse)

    assert sorted(yaml_files) == sorted(expected_yaml_files)


def test_get_yaml_files_file_input(mocker):
    name_yaml = "test.yaml"
    path_resolve_mock = mocker.patch("pathlib.Path.resolve", return_value=name_yaml)

    files = get_yaml_files(name_yaml, recursive=False)

    assert files == [name_yaml]
    path_resolve_mock.assert_called_once()


@pytest.mark.parametrize(
    "error,return_dir", [(FileNotFoundError, True), (ValueError, False)]
)
def test_get_yaml_files_errors(mocker, error, return_dir):
    path_is_dir_mock = mocker.patch("pathlib.Path.is_dir", return_value=return_dir)
    path_glob_mock = mocker.patch("pathlib.Path.glob", return_value=[])

    with pytest.raises(error):
        get_yaml_files(".", True)

    path_is_dir_mock.assert_called_once()
    if return_dir:
        path_glob_mock.assert_called_once_with("**/*.yaml")


def test_get_test_cases(mocker):
    cfg_dict = {"test_suite_list": None}
    basic_test_suite_mock = mocker.patch(
        "pykiso.test_coordinator.test_suite.BasicTestSuite"
    )
    basic_test_suite_mock._tests = ["test1", "test2"]
    collect_test_suite = mocker.patch(
        "pykiso.test_coordinator.test_execution.collect_test_suites",
        return_value=[basic_test_suite_mock, basic_test_suite_mock],
    )

    test_cases = get_test_cases(cfg_dict)

    assert test_cases == ["test1", "test2"] * 2
    collect_test_suite.assert_called_once_with(cfg_dict["test_suite_list"])


def test_get_test_cases_error():
    with pytest.raises(ValueError):
        get_test_cases({})


def test_get_test_tags(basic_test_mock):
    type(basic_test_mock).tag = PropertyMock(
        side_effect=[
            {"variant": ["variant1"], "branch_level": ["daily"]},
            {"variant": ["variant1"], "branch_level": ["daily"]},
            {"branch_level": ["nightly"], "variant": ["variant1"]},
            {"branch_level": ["nightly"], "variant": ["variant1"]},
            None,
        ],
    )

    tags = get_test_tags([basic_test_mock, basic_test_mock, basic_test_mock])

    assert {"variant": ["variant1"], "branch_level": ["daily", "nightly"]} == tags


@pytest.mark.parametrize("show_test_case", [True, False])
def test_build_result_dict(basic_test_mock, show_test_case):
    tags = {"variant": ["variant1"], "branch_level": ["daily", "nightly"]}
    config_file_name = "file_name"
    len_test = 5

    config_result_dict = build_result_dict(
        config_file_name, [basic_test_mock] * len_test, tags, show_test_case
    )

    config_expected = (
        {
            "File name": config_file_name,
            "Number of tests": len_test,
            "Test cases": ("unittest.mock.MagicMock\n" * (len_test - 1))
            + "unittest.mock.MagicMock",
            "variant": "variant1",
            "branch_level": "daily\nnightly",
        }
        if show_test_case
        else {
            "File name": config_file_name,
            "Number of tests": len_test,
            "variant": "variant1",
            "branch_level": "daily\nnightly",
        }
    )
    assert config_result_dict == config_expected


def test_tabulate_test_information():
    test_info = [
        {
            "File name": "dummy.yaml",
            "Number of tests": 9,
            "variant": "variant1\nvariant2\nvariant3",
            "branch_level": "daily\nnightly",
        }
    ]

    table_header, table_rows = tabulate_test_information(test_info)

    assert table_header == ["File name", "Number of tests", "variant", "branch_level"]
    assert table_rows == [
        ["dummy.yaml", 9, "variant1\nvariant2\nvariant3", "daily\nnightly"]
    ]


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_show_tag_main(tmp_path, tmp_test, runner):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [f"-c{tmp_test}"])

    assert (
        "\nAll valid configuration files have been processed successfully:"
        in result.output
    )

    assert (
        "╒════════════════╤═══════════════════╤═══════════╤════════════════╕\n"
        "│ File name      │   Number of tests │ variant   │ branch_level   │\n"
        "╞════════════════╪═══════════════════╪═══════════╪════════════════╡\n"
        "│ aux1_aux2.yaml │                 5 │ variant1  │ daily          │\n"
        "│                │                   │ variant2  │ nightly        │\n"
        "╘════════════════╧═══════════════════╧═══════════╧════════════════╛\n"
    ) in result.output
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "tmp_test,error_raised",
    [
        (("aux1", "aux2", False), ValueError("reason")),
        (("aux1", "aux2", False), TestCollectionError("reason")),
    ],
    indirect=["tmp_test"],
)
def test_show_tag_main_fail_get_test_case(
    tmp_path, tmp_test, error_raised, mocker, runner
):
    parse_config_mock = mocker.patch(
        "pykiso.tool.show_tag.get_test_cases", side_effect=error_raised
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [f"-c{tmp_test}"])

    assert "Failed to load test cases from config file" in result.output
    parse_config_mock.assert_called_once()
    assert result.exit_code == 1


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_show_tag_main_fail_parse_config(tmp_path, tmp_test, mocker, runner):
    parse_config_mock = mocker.patch("yaml.load", side_effect=ValueError())

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [f"-c{tmp_test}"])

    assert "Failed to parse config file" in result.output
    parse_config_mock.assert_called_once()
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "tmp_test,extension,function_to_patch",
    [
        (("aux1", "aux2", False), ".json", "json.dump"),
        (("aux1", "aux2", False), ".csv", "csv.writer"),
        (("aux1", "aux2", False), ".txt", "csv.writer"),
    ],
    indirect=["tmp_test"],
)
def test_show_tag_main_with_output(
    tmp_path, tmp_test, extension, function_to_patch, mocker, runner
):
    output_path = tmp_path / f"result{extension}"
    writer_mock = mocker.patch(function_to_patch)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [f"-c{tmp_test}", f"-o{output_path}"])

    assert f"Test configuration dumped to '{output_path}'" in result.output
    assert result.exit_code == 0
    if extension != ".txt":
        writer_mock.assert_called_once()
    else:
        with open(output_path, "r", encoding="utf-8") as f:
            assert f.readlines() == [
                "╒════════════════╤═══════════════════╤═══════════╤════════════════╕\n",
                "│ File name      │   Number of tests │ variant   │ branch_level   │\n",
                "╞════════════════╪═══════════════════╪═══════════╪════════════════╡\n",
                "│ aux1_aux2.yaml │                 5 │ variant1  │ daily          │\n",
                "│                │                   │ variant2  │ nightly        │\n",
                "╘════════════════╧═══════════════════╧═══════════╧════════════════╛",
            ]


@pytest.mark.parametrize("tmp_test", [("aux1", "aux2", False)], indirect=True)
def test_show_tag_main_output_format_unsupported(tmp_path, tmp_test, runner):
    output_suffixes = ".wrong_extension"
    output_path = tmp_path / f"result{output_suffixes}"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [f"-c{tmp_test}", f"-o{output_path}"])

    assert f"Unsupported export format {output_suffixes}" in result.output
    assert result.exit_code == 0


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

    cfg_dict = parse_config(tmp_test)
    test_cases = get_test_cases(cfg_dict)
    tags = get_test_tags(test_cases)
    single_config_result = build_result_dict(
        tmp_test.name, test_cases, tags, show_test_cases=True
    )
    all_results = [single_config_result]
    table_header, table_data = tabulate_test_information(all_results)

    assert table_header == list(expected_table_headers)
    assert table_data == list(expected_table_data)
