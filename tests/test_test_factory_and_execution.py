import pytest
import unittest
from pathlib import Path
from pykiso import test_factory_and_execution
from pykiso import cli
import logging

@pytest.fixture
def prepare_config():
    """return the configuration file path dummy.yaml
    """
    project_folder = Path.cwd()
    config_file_path = project_folder.joinpath('examples/dummy.yaml')
    return config_file_path

def test_test_factory_and_execution(prepare_config):
    """Call run method from test_factory_and_execution using
    configuration data comming from cli parse_config method

    Info: this test laod dummy.yaml configuration file present in exmaples folder

    Validation criteria:
        -  run is execute without error
    """
    cfg = cli.parse_config(prepare_config)
    test_factory_and_execution.run(cfg)
    