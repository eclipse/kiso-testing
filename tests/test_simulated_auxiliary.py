##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import queue
import re
import sys
from pathlib import Path

import pytest

from pykiso import cli, message
from pykiso.connector import CChannel
from pykiso.lib.auxiliaries.simulated_auxiliary import (
    scenario,
    simulated_auxiliary,
    simulation,
)
from pykiso.test_coordinator import test_execution
from pykiso.test_setup.config_registry import ConfigRegistry

ACK = message.MessageType.ACK
ABORT = message.MessageCommandType.ABORT
PING = message.MessageCommandType.PING

expected_failures = [
    (
        "test_suite_setUp",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_setUp",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:21, type:2, error_code:0, reserved:0, test_suite ID:4, test_case ID:0!",
    ),
    (
        "test_suite_setUp",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:28, type:2, error_code:0, reserved:0, test_suite ID:5, test_case ID:0!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:71, type:3, error_code:0, reserved:0, test_suite ID:1, test_case ID:4!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:78, type:3, error_code:0, reserved:0, test_suite ID:1, test_case ID:5!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:145, type:13, error_code:0, reserved:0, test_suite ID:1, test_case ID:8!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:168, type:13, error_code:0, reserved:0, test_suite ID:1, test_case ID:9!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_run",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:251, type:23, error_code:0, reserved:0, test_suite ID:1, test_case ID:12!",
    ),
    (
        "test_run",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:18, type:23, error_code:0, reserved:0, test_suite ID:1, test_case ID:13!',)",
    ),
    (
        "test_run",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_tearDown",
        "<MessageReportType.TEST_FAILED: 1> != <MessageReportType.TEST_PASS: 0>",
    ),
    (
        "test_suite_tearDown",
        "No response received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command : msg_type:0, message_token:69, type:22, error_code:0, reserved:0, test_suite ID:8, test_case ID:0!",
    ),
    (
        "test_suite_tearDown",
        "('No report received from DUT for auxiliairy : <aux_udp is ExampleAuxiliary(aux_udp, started 19804)> command :msg_type:0, message_token:76, type:22, error_code:0, reserved:0, test_suite ID:9, test_case ID:0!',)",
    ),
]


@pytest.fixture
def prepare_config():
    """return the configuration file path virtual.yaml"""
    project_folder = Path.cwd()
    config_file_path = project_folder / "examples/virtual.yaml"
    return config_file_path


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
    return {"msg": msg}


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
    mock_msg["msg"].msg_type = ACK
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
    assert return_receive_message == mock_msg["msg"]


def test_send_responses(mocker, simulated_constructor_init, mock_msg):
    simulated_aux = simulated_constructor_init
    responses = ["test", "test2"]
    simulated_aux._send_responses(responses)
    simulated_aux.channel._cc_send.assert_called()
    assert simulated_aux.channel._cc_send.call_count == 2


@pytest.mark.skip(reason="Needs to be fixed")
@pytest.mark.slow
def test_virtual_cfg_output(capsys, prepare_config):
    """run the 'virtual.yaml' configuration and compare it to
    expected outputs.

    The outputs are pre-generated and we just ensure that they don't
    change arbitrarily.
    """
    cfg = cli.parse_config(prepare_config)
    with pytest.raises(SystemExit):
        ConfigRegistry.register_aux_con(cfg)
        exit_code = test_execution.execute(cfg)
        ConfigRegistry.delete_aux_con()
        sys.exit(exit_code)

    output = capsys.readouterr()
    assert "F.FFF.FFF.FFF.FF..FF.FF" in output.err
    pattern = r"=+\s+FAIL: (\w+)\s+.*?AssertionError: ([^\n]+)$"
    failures = [
        m.groups() for m in re.finditer(pattern, output.err, re.MULTILINE + re.DOTALL)
    ]

    drop_aux_pattern = re.compile(r"auxiliairy : <.*?>")
    drop_token_pattern = re.compile(r"message_token:\d+")

    for (res_place, res_err), (ex_place, ex_err) in zip(failures, expected_failures):
        assert res_place == ex_place
        # remove aux field as that contains information that changes from run to run
        actual_error = drop_aux_pattern.sub("auxiliary : REMOVED", res_err)
        actual_error = drop_token_pattern.sub("message_toke:REMOVED", actual_error)
        expected_error = drop_aux_pattern.sub("auxiliary : REMOVED", ex_err)
        expected_error = drop_token_pattern.sub("message_toke:REMOVED", expected_error)
        assert actual_error == expected_error
