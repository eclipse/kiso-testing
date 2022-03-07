##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import os
from collections import namedtuple
from pathlib import Path

import pytest

from pykiso.config_parser import check_requirements, parse_config


@pytest.fixture
def tmp_cfg(tmp_path):
    """Create following test folder inside tmp_dir
    tmp_dir
    │
    │── cc_config
    │   │   cc_config.elf
    │
    |── ext_lib
    │   │   import_connector.py
    │
    └── tests
        │   aux1.yaml
        │
        │── test_suite_aux1
        │
        └── suite_config
            │   suite_conf.yaml
    """
    # create tests folder at root
    test_folder = tmp_path / "tests"
    test_folder.mkdir()
    # create test suite inside tests folder
    testsuite_folder = test_folder / "test_suite_aux1"
    testsuite_folder.mkdir()
    # create suite config folder
    suite_config_folder = test_folder / "suite_config"
    suite_config_folder.mkdir()
    # create cc_config folder at root
    cc_config_folder = tmp_path / "cc_config"
    cc_config_folder.mkdir()
    # create any config file inside cc_config folder
    cc_config_file = cc_config_folder / "cc_config.elf"
    cc_config_file.write_text("Some config")
    # create ext_lib folder at root
    ext_lib_folder = tmp_path / "ext_lib"
    ext_lib_folder.mkdir()
    # create import_connector.py file inside ext_lib
    ext_lib_file = ext_lib_folder / "import_connector.py"
    ext_lib_file.write_text("Some connector")
    # set paths in config file
    config_paths = {
        "root": tmp_path,
        "testsuite": testsuite_folder,
        "suite_config": suite_config_folder,
        "cc_config": cc_config_file,
        "ext_lib": ext_lib_file,
    }
    # create config file
    config_file = test_folder / "aux1.yaml"
    suite_config_file = suite_config_folder / "suite_conf.yaml"
    cfg_content = create_config(config_paths)
    suite_cfg_content = create_suite_config(config_paths)
    config_file.write_text(cfg_content)
    suite_config_file.write_text(suite_cfg_content)

    return config_file


@pytest.fixture
def tmp_cfg_mod(tmp_cfg):
    """Inherit folder structure from tmp_cfg.
    Rename folder tests->CMP and replace content of aux1.yaml
    tmp_dir
    │
    │── cc_config
    │   │   cc_config.elf
    │
    |── ext_lib
    │   │   import_connector.py
    │
    └── COMP1
        │   aux1.yaml
        │
        │── test_suite_aux1
        │
        └── suite_config
            │   suite_conf.yaml

    """
    test_folder = tmp_cfg.parent.parent / "CMP"
    os.rename(tmp_cfg.parent, test_folder)
    cfg_content = create_simple_config()
    config_file = test_folder / "aux1.yaml"
    config_file.write_text(cfg_content)
    return config_file


@pytest.fixture
def tmp_cfg_env_var(tmp_path):
    """Inherit folder structure from tmp_cfg."""
    cfg_content = create_env_var_config()
    config_file = tmp_path / "aux1.yaml"
    config_file.write_text(cfg_content)
    return config_file


@pytest.fixture
def tmp_cfg_folder_conflict(tmp_path):
    """Inherit folder structure from tmp_cfg."""
    cfg_content = create_config_folder_conflict()
    conflict_folder = tmp_path / "aux1"
    conflict_folder.mkdir()
    config_file = tmp_path / "aux1.yaml"
    config_file.write_text(cfg_content)
    return config_file


def create_simple_config():
    cfg = """
auxiliaries:
  aux1:
    connectors:
        com:   chan1
        flash: chan2
    config: null
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
connectors:
  chan1:
    config: null
    type: ext_lib/cc_example.py:CCExample
    """
    return cfg


def create_config(paths):
    # create base config file located in tests/aux1.yaml
    cfg = (
        """
auxiliaries:
  aux1:
    connectors:
        com:   chan1
        flash: chan2
    config: null
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
connectors:
  chan1:
    type: """
        + str(paths["ext_lib"])
        + ":CCExample"
        + """
    config:
        configPath: """
        + str(paths["cc_config"])
        + """
  chan2:
    type: """
        + str(Path("../ext_lib/import_connector.py:CCExample"))
        + """
    config:
        configPath: """
        + str(Path("../cc_config/cc_config.elf"))
        + """
  chan3:
    type: ../ext_lib/import_connector.py:CCExample
    config:
        configPath: """
        + str(Path("../invalid:path"))
        + """
  chan4:
    type: ../ext_lib/import_connector.py:CCExample
    config:
        configPath: ENV{CC_CONFIG}
test_suite_list: !include """
        + str(paths["suite_config"] / "suite_conf.yaml")
        + """
requirements:
  - pykiso: ">=0.0.0"
    """
    )
    return cfg


def create_suite_config(paths):
    # create nested config file located in tests/suite_config/suite_conf.yaml
    cfg = (
        """
- suite_dir: """
        + str(paths["testsuite"])
        + """
  test_filter_pattern: '*.py'
  test_suite_id: 1
- suite_dir: ../test_suite_aux1
  test_filter_pattern: '*.py'
  test_suite_id: 2
- suite_dir: ENV{TEST_SUITE_1}
  test_filter_pattern: '*.py'
  test_suite_id: 3
    """
    )
    return cfg


def create_env_var_config():
    cfg = """
auxiliaries:
  aux1:
    connectors:
        com: chan1
    config: null
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
connectors:
  chan1:
    config:
      some_bool: ENV{bool_env_var}
      some_string: ENV{str_env_var}
      some_integer: 'ENV{int_env_var}'
      some_integer_as_hex:  "ENV{int_env_var_as_hex}"
      some_path: 'ENV{path_env_var}'
      some_path_default_value: 'ENV{path_env_var_set=/examples/path}'
      some_path_default_value_relative: 'ENV{path_env_var_not_set=./test_suite_aux1}'
      some_path_env_variable_not_set: 'ENV{path_env_var_not_set=/examples/path2}'
      some_path_env_error: 'ENV{path_env_var_not_set}'
    type: pykiso.lib.connectors.cc_example::CCExample
    """
    return cfg


def create_config_folder_conflict():
    cfg = """
auxiliaries:
  aux1:
    absPath: ./aux1
    config: 'aux1'
    ENV{config}: config
    type: pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary
connectors:
  chan1:
    config:
      some_bool: True
    type: pykiso.lib.connectors.cc_example::CCExample
    """
    return cfg


def test_parse_config(tmp_cfg, tmp_path, mocker, caplog):

    mocker.patch.dict(
        os.environ,
        {
            "TEST_SUITE_1": str(tmp_path / "tests/test_suite_aux1"),
            "CC_CONFIG": str(tmp_path / "cc_config/cc_config.elf"),
        },
    )
    mock_check_req = mocker.patch("pykiso.config_parser.check_requirements")

    with caplog.at_level(logging.DEBUG):
        cfg = parse_config(tmp_cfg)

    mock_check_req.assert_called_once_with([{"pykiso": ">=0.0.0"}])

    # Test _fix_types_loc
    assert "Resolved path :" in caplog.text
    assert (
        cfg["auxiliaries"]["aux1"]["type"]
        == "pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary"
    )
    assert cfg["connectors"]["chan1"]["type"] == str(
        tmp_path / "ext_lib" / "import_connector.py:CCExample"
    )
    assert cfg["connectors"]["chan2"]["type"] == str(
        tmp_path / "ext_lib" / "import_connector.py:CCExample"
    )

    # Test _resolve_path and _parse_env_var for test_suite
    assert "Resolved relative path" in caplog.text
    assert "Replaced environment variable TEST_SUITE_1" in caplog.text
    for testsuite in cfg["test_suite_list"]:
        assert str(testsuite["suite_dir"]) == str(
            tmp_path / "tests" / "test_suite_aux1"
        )
        assert Path(testsuite["suite_dir"]).is_absolute()

    # Test _parse_env_var for connectors
    assert "Replaced environment variable CC_CONFIG" in caplog.text
    assert str(cfg["connectors"]["chan4"]["config"]["configPath"]) == str(
        tmp_path / "cc_config" / "cc_config.elf"
    )

    # Test _resolve_path with absolute and relative paths
    assert "Resolved relative path" in caplog.text
    assert Path(cfg["connectors"]["chan1"]["config"]["configPath"]).is_absolute()
    assert Path(cfg["connectors"]["chan2"]["config"]["configPath"]).is_absolute()
    assert str(cfg["connectors"]["chan1"]["config"]["configPath"]) == str(
        tmp_path / "cc_config" / "cc_config.elf"
    )
    assert str(cfg["connectors"]["chan2"]["config"]["configPath"]) == str(
        tmp_path / "cc_config" / "cc_config.elf"
    )

    # Test with invalid path
    assert not Path(cfg["connectors"]["chan3"]["config"]["configPath"]).is_absolute()
    assert Path(cfg["connectors"]["chan3"]["config"]["configPath"]) == Path(
        "../invalid:path"
    )


def test_parse_config_env_var(tmp_cfg_env_var, mocker, tmp_path):

    mocker.patch.dict(
        os.environ,
        {
            "bool_env_var": "True",
            "str_env_var": "this is a string",
            "int_env_var": "1234567890",
            "int_env_var_as_hex": "0x0123456789aBcDef",
            "path_env_var": f"{tmp_path}",
            "path_env_var_set": f"{tmp_path}",
        },
    )

    # some_path_env_error should raise a ValueError
    with pytest.raises(ValueError):
        cfg = parse_config(tmp_cfg_env_var)

        assert cfg["connectors"]["chan1"]["config"]["some_bool"] == True
        assert cfg["connectors"]["chan1"]["config"]["some_string"] == "this is a string"
        assert cfg["connectors"]["chan1"]["config"]["some_integer"] == 1234567890
        assert (
            cfg["connectors"]["chan1"]["config"]["some_integer_as_hex"]
            == 0x0123456789ABCDEF
        )
        assert cfg["connectors"]["chan1"]["config"]["some_path"] == str(tmp_path)
        assert Path(
            cfg["connectors"]["chan1"]["config"]["some_path_default_value"]
        ).is_absolute()
        assert cfg["connectors"]["chan1"]["config"][
            "some_path_default_value_relative"
        ] == str(tmp_path)
        assert (
            cfg["connectors"]["chan1"]["config"]["some_path_env_variable_not_set"]
            == "/examples/path2"
        )


def test_parse_config_folder_name_eq_entity_name(tmp_cfg_mod):

    cfg = parse_config(tmp_cfg_mod)

    assert not cfg["auxiliaries"]["aux1"]["config"]


def test_parse_config_folder_conflict(tmp_cfg_folder_conflict, tmp_path, caplog):
    # test foldername conflict when key in cfg matches an existing folder
    # separating a cfg value from an existing matching folder is impossible
    # without enforcing ./ notation or putting the value in single quotes
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    with caplog.at_level(logging.DEBUG):
        cfg = parse_config(tmp_cfg_folder_conflict)

    # key should not be parsed if it matches a folder/file
    assert "aux1" in cfg["auxiliaries"]
    # value should not be parsed if it is enclosed in single quotes
    assert "aux1" == cfg["auxiliaries"]["aux1"]["config"]
    # key should not be parsed if it matches the env var pattern
    assert "ENV{config}" in cfg["auxiliaries"]["aux1"]
    # value should be parsed
    assert Path(cfg["auxiliaries"]["aux1"]["absPath"]).is_absolute()
    os.chdir(old_cwd)


@pytest.mark.parametrize(
    "requirements, mock_installed_versions, exit_reason",
    [
        # test simple specification
        pytest.param(
            [{"pykiso": "0.9.4"}],
            {"pykiso": "0.9.4"},
            None,
            id="static version: minimum version installed",
        ),
        pytest.param(
            [{"pykiso": "0.9.4"}],
            {"pykiso": "0.9.3"},
            "'0.9.3' instead of '0.9.4' (minimum)",
            id="static version: lower version installed",
        ),
        pytest.param(
            [{"pykiso": "0.9.4"}],
            {"pykiso": "0.9.5"},
            None,
            id="static version: higher version installed",
        ),
        pytest.param(
            [{"pykiso": "any"}], {"pykiso": "0.9.5"}, None, id="static version: any"
        ),
        # test condition
        pytest.param(
            [{"pykiso": "==0.9.4"}],
            {"pykiso": "0.9.5"},
            "'0.9.5' but '==0.9.4' given",
            id="single condition strict: installed version too high",
        ),
        ([{"pykiso": "==0.9.4"}], {"pykiso": "0.9.4"}, None),
        pytest.param(
            [{"pykiso": "<=0.9.4"}],
            {"pykiso": "0.9.5"},
            "'0.9.5' but '<=0.9.4' given",
            id="single condition lower-equal: installed is too high",
        ),
        pytest.param([{"pykiso": "<=0.9.4"}], {"pykiso": "0.9.4"}, None),
        pytest.param(
            [{"pykiso": ">=0.9.6"}],
            {"pykiso": "0.9.5"},
            "'0.9.5' but '>=0.9.6' given",
            id="single condition higher-equal: installed is too low",
        ),
        pytest.param([{"pykiso": ">=0.9.5"}], {"pykiso": "0.9.5"}, None),
        ([{"pykiso": ">0.9.5"}], {"pykiso": "0.9.5"}, "'0.9.5' but '>0.9.5' given"),
        pytest.param([{"pykiso": ">0.9.5"}], {"pykiso": "0.9.6"}, None),
        pytest.param(
            [{"pykiso": "<0.9.5"}],
            {"pykiso": "0.9.5"},
            "'0.9.5' but '<0.9.5' given",
            id="single condition lower: installed is equal",
        ),
        pytest.param(
            [{"pykiso": "<0.9.5"}],
            {"pykiso": "0.9.4"},
            None,
            id="single condition lower: installed is lower",
        ),
        pytest.param(
            [{"pykiso": "<<0.9.5"}],
            {"pykiso": "0.9.4"},
            "comparator '<<' not among ['<', '<=', '>', '>=', '==', '!=']",
            id="single condition equal: invalid comparator",
        ),
        pytest.param(
            [{"pykiso": "== 0.9.5"}],
            {"pykiso": "0.9.4"},
            "'0.9.4' but '== 0.9.5' given",
            id="single condition strict (stripped): installed is lower",
        ),
        pytest.param(
            [{"pykiso": "== 0.9.5"}],
            {"pykiso": "0.9.5"},
            None,
            id="single condition equal (stripped): installed is equal",
        ),
        pytest.param(
            [{"pykiso": "!= 0.9.5"}],
            {"pykiso": "0.9.5"},
            "'0.9.5' but '!= 0.9.5' given",
            id="single condition different (stripped): installed is equal",
        ),
        # test multi requirements
        pytest.param(
            [{"pykiso": ">=0.9.5,<0.10.1"}],
            {"pykiso": "0.9.4"},
            "'0.9.4' but '>=0.9.5,<0.10.1' given",
            id="multi condition: installed not in range (too low)",
        ),
        pytest.param(
            [{"pykiso": ">=0.9.5, <0.10.1"}],
            {"pykiso": "0.10.1"},
            "'0.10.1' but '>=0.9.5, <0.10.1' given",
            id="multi condition: installed not in range (too high)",
        ),
        pytest.param(
            [{"pykiso": ">=0.9.5,<0.10.1"}],
            {"pykiso": "0.10.0"},
            None,
            id="multi condition: installed in range",
        ),
        pytest.param(
            [{"package_a": ">=1.a"}, {"package_b": "1.2.3"}],
            {"package_a": "1.b", "package_b": "1.2.3"},
            None,
            id="multi package: installed ok",
        ),
    ],
)
def test_check_requirements(
    requirements, mock_installed_versions, caplog, exit_reason, mocker
):
    Version = namedtuple("Version", "version")

    def get_version(package):
        return Version(mock_installed_versions[package])

    mocker.patch("pkg_resources.get_distribution", new=get_version)
    mock_exit = mocker.patch("sys.exit")

    with caplog.at_level(logging.INFO):
        check_requirements(requirements)

    if exit_reason:
        mock_exit.assert_called_once_with(1)
        assert exit_reason in caplog.text
    else:
        mock_exit.assert_not_called()


def test_check_requirements_package(caplog, mocker):
    mock_exit = mocker.patch("sys.exit")

    with caplog.at_level(logging.INFO):
        check_requirements([{"not_installed_package": "1.2.3"}])

    mock_exit.assert_called_once_with(1)
    assert "not_installed_package not found" in caplog.text
