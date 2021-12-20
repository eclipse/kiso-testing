##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.proxy_auxiliary import (
    MpProxyAux,
    MpProxyAuxiliary,
    ProxyAux,
    ProxyAuxiliary,
)
from pykiso.test_setup.config_registry import ConfigRegistry


@pytest.fixture(scope="function")
def robot_proxy_aux(mocker, cchannel_inst):
    mocker.patch.object(ProxyAux, "run")
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"proxy": ProxyAux(cchannel_inst, [])},
    )
    return ProxyAuxiliary()


@pytest.fixture(scope="function")
def proxy_aux(robot_proxy_aux):
    return robot_proxy_aux._get_aux("proxy")


def test_suspend(mocker, robot_proxy_aux, proxy_aux):
    suspend_mock = mocker.patch.object(proxy_aux, "suspend")

    robot_proxy_aux.suspend("proxy")

    suspend_mock.assert_called_once()


def test_resume(mocker, robot_proxy_aux, proxy_aux):
    resume_mock = mocker.patch.object(proxy_aux, "resume")

    robot_proxy_aux.resume("proxy")

    resume_mock.assert_called_once()


def robot_mp_proxy_aux(mocker, cchannel_inst):
    mocker.patch.object(MpProxyAux, "run")
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"proxy": MpProxyAux(cchannel_inst, [])},
    )
    return ProxyAuxiliary()


@pytest.fixture(scope="function")
def mp_proxy_aux(robot_mp_proxy_aux):
    return robot_proxy_aux._get_aux("proxy")


def test_mp_suspend(mocker, robot_proxy_aux, proxy_aux):
    suspend_mock = mocker.patch.object(proxy_aux, "suspend")

    robot_proxy_aux.suspend("proxy")

    suspend_mock.assert_called_once()


def test_mp_resume(mocker, robot_proxy_aux, proxy_aux):
    resume_mock = mocker.patch.object(proxy_aux, "resume")

    robot_proxy_aux.resume("proxy")

    resume_mock.assert_called_once()
