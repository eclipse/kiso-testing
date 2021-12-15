##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import sys

import pytest

from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.robot_framework.loader import RobotLoader, parse_config


@pytest.fixture
def robot_config():
    config = {
        "auxiliaries": {
            "aux_com_1": {
                "connectors": {"com": "chan1"},
                "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            },
            "aux_com_2": {
                "connectors": {"com": "chan2"},
                "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            },
        },
        "connectors": {
            "chan1": {"type": "pykiso.lib.connectors.cc_raw_loopback:CCLoopback"},
            "chan2": {"type": "pykiso.lib.connectors.cc_raw_loopback:CCLoopback"},
        },
    }
    return config


@pytest.fixture
def robot_proxy_config():
    config = {
        "auxiliaries": {
            "aux_com_1": {
                "connectors": {"com": "chan1"},
                "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            },
            "aux_com_2": {
                "connectors": {"com": "chan2"},
                "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            },
            "aux_proxy_com": {
                "connectors": {"com": "chan3"},
                "config": {"aux_list": ["aux1", "aux2"]},
                "type": "pykiso.lib.auxiliaries.proxy_auxiliary:ProxyAuxiliary",
            },
        },
        "connectors": {
            "chan1": {"type": "pykiso.lib.connectors.cc_proxy:CCProxy"},
            "chan2": {"type": "pykiso.lib.connectors.cc_proxy:CCProxy"},
            "chan3": {"type": "pykiso.lib.connectors.cc_raw_loopback:CCLoopback"},
        },
    }
    return config


@pytest.fixture
def loader_instance(mocker, robot_config):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.parse_config", return_value=robot_config
    )
    loader_inst = RobotLoader(robot_config)
    return loader_inst


@pytest.fixture
def loader_proxy_instance(mocker, robot_proxy_config):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.parse_config",
        return_value=robot_proxy_config,
    )
    loader_inst = RobotLoader(robot_proxy_config)
    return loader_inst


def test_detect_proxy_auxes_without_proxy(loader_instance):
    proxy_list = loader_instance._detect_proxy_auxes()

    assert not proxy_list


def test_detect_proxy_auxes_with_proxy(loader_proxy_instance):
    proxy_list = loader_proxy_instance._detect_proxy_auxes()

    assert proxy_list
    assert proxy_list.pop() == "aux_proxy_com"


def test_install_without_proxy(mocker, loader_instance, robot_config):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.register_aux_con",
        return_value=None,
    )
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.get_auxes_alias",
        return_value=robot_config["auxiliaries"].keys(),
    )
    import_mock = mocker.patch("importlib.import_module", return_value=True)
    loader_instance.install()

    import_mock.assert_called()
    assert loader_instance.auxiliaries["aux_com_1"]
    assert loader_instance.auxiliaries["aux_com_2"]


def test_install_with_proxy(mocker, loader_proxy_instance, robot_proxy_config):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.register_aux_con",
        return_value=None,
    )
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.get_auxes_alias",
        return_value=robot_proxy_config["auxiliaries"].keys(),
    )
    import_mock = mocker.patch("importlib.import_module", return_value=True)
    loader_proxy_instance.install()

    import_mock.assert_called()
    assert loader_proxy_instance.auxiliaries["aux_com_1"]
    assert loader_proxy_instance.auxiliaries["aux_com_2"]
    assert loader_proxy_instance.auxiliaries["aux_proxy_com"]


def test_install_exception(mocker, loader_instance):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.register_aux_con",
        side_effect=ValueError,
    )

    with pytest.raises(ValueError):
        loader_instance.install()


def test_uninstall(mocker, loader_instance, robot_config):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.delete_aux_con",
        return_value=None,
    )
    loader_instance.auxiliaries["pytest_fake_aux"] = None
    sys.modules["pykiso.auxiliaries.pytest_fake_aux"] = None

    loader_instance.uninstall()

    assert "pykiso.auxiliaries.pytest_fake_aux" not in sys.modules.keys()


def test_uninstall_exception(mocker, loader_instance):
    mocker.patch(
        "pykiso.lib.robot_framework.loader.ConfigRegistry.delete_aux_con",
        side_effect=ValueError,
    )

    with pytest.raises(ValueError):
        loader_instance.uninstall()
