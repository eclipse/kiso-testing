##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import pytest
from pykiso import message
from pykiso.connector import CChannel
import queue
from pykiso.lib.auxiliaries.simulated_auxiliary import (
    simulated_auxiliary,
    scenario,
    simulation,
)

ACK = message.MessageType.ACK
ABORT = message.MessageCommandType.ABORT
PING = message.MessageCommandType.PING


@pytest.fixture
def mock_channel(mocker):
    class MockProxyCChannel(CChannel):
        def __init__(self, name=None, *args, **kwargs):
            self.name = name
            self.queue_in = queue.Queue()
            self.queue_out = queue.Queue()
            super(MockProxyCChannel, self).__init__(*args, **kwargs)

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")

    return MockProxyCChannel(name="test_aux")


@pytest.fixture
def simulated_constructor_init(mocker, mock_channel, mock_msg):
    class Dict_modified(dict):
        def __init__(self):
            super().__init__()

        def get_scenario(self, test_suite_id: int, test_case_id: int):
            return scenario.Scenario([None])

    mocker.patch.object(simulation.Simulation, "__init__", return_value=None)
    proxy_inst = simulated_auxiliary.SimulatedAuxiliary(
        name="test_aux",
        com=mock_channel,
    )
    proxy_inst.context = Dict_modified()
    return proxy_inst


@pytest.fixture
def mock_msg(mocker):
    msg = message.Message
    msg.msg_type = ABORT
    msg.sub_type = ACK
    msg.test_suite = 1
    msg.test_case = 1
    return msg


def test_constructor(mocker, caplog):
    mocker.patch.object(simulation.Simulation, "__init__", return_value=None)

    with caplog.at_level(
        logging.DEBUG,
    ):
        simulated_aux = simulated_auxiliary.SimulatedAuxiliary(
            name="test_aux",
        )

    assert "com is None" in caplog.text
    assert simulated_aux.name == "test_aux"
    assert simulated_aux.playbook is None
    assert simulated_aux.ts_tc is None


def test_create_auxiliary_instance(mocker, simulated_constructor_init, caplog):
    simulated_aux = simulated_constructor_init

    mocker.patch.object(simulated_aux, "channel")

    with caplog.at_level(
        logging.INFO,
    ):
        result_create_inst = simulated_aux._create_auxiliary_instance()
    assert result_create_inst is True
    assert "Create auxiliary instance" in caplog.text
    assert "Enable channel" in caplog.text


def test_delete_auxiliary_instance(mocker, simulated_constructor_init, caplog):
    simulated_aux = simulated_constructor_init
    mock_channel_close = mocker.patch.object(simulated_aux.channel, "close")
    with caplog.at_level(
        logging.INFO,
    ):
        result_del_inst = simulated_aux._delete_auxiliary_instance()
    assert result_del_inst is True
    assert "Delete auxiliary instance" in caplog.text
    mock_channel_close.assert_called()


def test_receive_message_ack_received(mocker, simulated_constructor_init, mock_msg):
    simulated_aux = simulated_constructor_init
    mock_msg.msg_type = ACK
    mocker_cc_receive = mocker.patch(
        "pykiso.connector.CChannel.cc_receive", return_value=mock_msg
    )
    simulated_aux._receive_message(2)
    mocker_cc_receive.assert_called()


def test_receive_message_no_ack_received(mocker, simulated_constructor_init, mock_msg):
    simulated_aux = simulated_constructor_init

    mock_send_responses = mocker.patch.object(
        simulated_auxiliary.SimulatedAuxiliary, "_send_responses"
    )

    mocker_cc_receive = mocker.patch(
        "pykiso.connector.CChannel.cc_receive", return_value=mock_msg
    )
    return_receive_message = simulated_aux._receive_message(2)
    mocker_cc_receive.assert_called()
    mock_send_responses.assert_called()
    assert return_receive_message == mock_msg


def test_send_responses(mocker, simulated_constructor_init, mock_msg):
    simulated_aux = simulated_constructor_init
    responses = ["test", "test2"]
    simulated_aux._send_responses(responses)
    simulated_aux.channel._cc_send.assert_called()
    assert simulated_aux.channel._cc_send.call_count == 2
