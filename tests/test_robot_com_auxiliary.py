##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.robot_framework.communication_auxiliary import (
    ComAux,
    CommunicationAuxiliary,
)


@pytest.fixture
def communication_aux_instance(mocker):
    mocker.patch(
        "pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run", return_value=None
    )
    mocker.patch(
        "pykiso.test_setup.config_registry.ConfigRegistry.get_auxes_by_type",
        return_value={"itf_com_aux": ComAux("channel")},
    )
    return CommunicationAuxiliary()


def test_send_message(mocker, communication_aux_instance):
    send_msg_mock = mocker.patch.object(ComAux, "send_message", return_value=True)

    state = communication_aux_instance.send_message(b"\x01\x02\x03", "itf_com_aux")

    assert state
    send_msg_mock.assert_called_once()


def test_get_message_without_source(mocker, communication_aux_instance):
    receive_msg_mock = mocker.patch.object(
        ComAux, "receive_message", return_value=b"\x01\x02\x03"
    )

    msg, source = communication_aux_instance.receive_message("itf_com_aux", True, 10.0)

    receive_msg_mock.assert_called_once()
    assert isinstance(msg, list)
    assert source is None
    assert msg == [1, 2, 3]


def test_get_message_with_source(mocker, communication_aux_instance):
    receive_msg_mock = mocker.patch.object(
        ComAux, "receive_message", return_value=(b"\x01\x02\x03", 0x123)
    )

    msg, source = communication_aux_instance.receive_message("itf_com_aux", True, 10.0)

    receive_msg_mock.assert_called_once()
    assert isinstance(msg, list)
    assert source == 0x123
    assert msg == [1, 2, 3]
