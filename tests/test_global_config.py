##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import click
import pytest

from pykiso.global_config import GlobalConfig, Grabber, ProtectedNamespace

yaml_config = {
    "auxiliaries": {
        "aux1": {
            "connectors": {"com": "chan1"},
            "config": None,
            "type": "..\\examples\\ext_lib\\example_test_auxiliary.py:ExampleAuxiliary",
        },
        "aux2": {
            "connectors": {"com": "chan2", "flash": "chan3"},
            "type": "pykiso.lib.auxiliaries.example_test_auxiliary:ExampleAuxiliary",
        },
        "aux3": {
            "connectors": {"com": "chan4"},
            "type": "pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary",
        },
    },
    "connectors": {
        "chan1": {
            "config": None,
            "type": "..\\examples\\ext_lib\\cc_example.py:CCExample",
        },
        "chan2": {"type": "..\\examples\\ext_lib\\cc_example.py:CCExample"},
        "chan4": {"type": "..\\examples\\ext_lib\\cc_example.py:CCExample"},
        "chan3": {
            "config": {"param_1": "value 1", "param_2": 2000},
            "type": "..\\examples\\ext_lib\\cc_example.py:CCExample",
        },
    },
    "test_suite_list": [
        {
            "suite_dir": "..\\examples\\conf_access",
            "test_filter_pattern": "*.py",
            "test_suite_id": 1,
        }
    ],
}


@pytest.fixture
def config_instance(mocker):
    @Grabber.grab_yaml_config
    def config_parser():
        return yaml_config

    @Grabber.grab_cli_config
    def cli_parser(
        click_context: click.Context,
        test_configuration_file,
        log_path,
        log_level,
        report_type,
        pattern,
    ):
        return None

    config_parser()
    context_mock = mocker.patch("click.Context")
    context_mock.args = ["--variant", "variant1,variant2", "--branch-level", "daily"]

    cli_parser(
        click_context=context_mock,
        test_configuration_file="examples/conf_access.yaml",
        log_path=None,
        log_level="INFO",
        report_type="text",
        pattern=None,
    )
    return GlobalConfig()


def test_singleton_implemetation(config_instance):
    other_conf = GlobalConfig()
    import logging

    logging.error(other_conf.cli)
    assert config_instance == other_conf
    assert config_instance.yaml.auxiliaries == other_conf.yaml.auxiliaries
    assert config_instance.yaml.connectors == other_conf.yaml.connectors
    assert config_instance.yaml.test_suite_list == other_conf.yaml.test_suite_list
    assert (
        config_instance.cli.test_configuration_file
        == other_conf.cli.test_configuration_file
    )
    assert config_instance.cli.log_path == other_conf.cli.log_path
    assert config_instance.cli.log_level == other_conf.cli.log_level
    assert config_instance.cli.report_type == other_conf.cli.report_type
    assert config_instance.cli.variant == other_conf.cli.variant
    assert config_instance.cli.branch_level == other_conf.cli.branch_level
    assert config_instance.cli.pattern == other_conf.cli.pattern


def test_grabber(config_instance):
    assert config_instance.cli.log_path == None
    assert config_instance.cli.log_level == "INFO"
    assert config_instance.cli.report_type == "text"
    assert config_instance.cli.variant == ["variant1", "variant2"]
    assert config_instance.cli.branch_level == ["daily"]
    assert config_instance.cli.pattern == None


def test_writing_forbidden(config_instance):
    with pytest.raises(AttributeError):
        config_instance.yaml.auxiliaries = "value"
