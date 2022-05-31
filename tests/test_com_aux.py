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

from pykiso import Message
from pykiso.lib.auxiliaries.communication_auxiliary import (
    CommunicationAuxiliary,
)
from pykiso.test_setup.dynamic_loader import DynamicImportLinker


@pytest.fixture
def com_aux_init(cchannel_inst):
    com_aux = CommunicationAuxiliary(
        name="mp_aux",
        com=cchannel_inst,
    )
    return com_aux


@pytest.fixture
def return_test():
    return "test"


@pytest.fixture
def com_aux_linker():
    linker = DynamicImportLinker()
    aux_conf = {
        "com_aux": {
            "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            "connectors": {"com": "loopback"},
        },
    }
    con_conf = {
        "loopback": {"type": "pykiso.lib.connectors.cc_raw_loopback:CCLoopback"}
    }
    for connector, con_details in con_conf.items():
        cfg = con_details.get("config") or dict()
        linker.provide_connector(connector, con_details["type"], **cfg)
    for auxiliary, aux_details in aux_conf.items():
        cfg = aux_details.get("config") or dict()
        linker.provide_auxiliary(
            auxiliary,
            aux_details["type"],
            aux_cons=aux_details["connectors"],
            **cfg,
        )
    linker.install()
    yield linker
    linker.uninstall()


def test_com_aux_messaging(com_aux_linker, caplog):
    from pykiso.auxiliaries import com_aux

    msg = b"test"
    assert com_aux.send_message(msg)
    with caplog.at_level(logging.DEBUG):
        rec_msg = com_aux.receive_message()
    assert rec_msg == msg
    assert com_aux.is_proxy_capable
    assert (
        f"retrieving message in {com_aux} (blocking={True}, timeout={None})"
        in caplog.text
    )


@pytest.mark.parametrize(
    "side_effect_mock, log_level, expected_log_1, expected_log_2, expected_function_return",
    [
        (None, logging.INFO, "Create auxiliary instance", "Enable channel", True),
        (
            Exception,
            logging.ERROR,
            "Unable to open channel communication",
            " ",
            False,
        ),
    ],
)
def test_create_auxiliary_instance(
    mocker,
    com_aux_init,
    caplog,
    side_effect_mock,
    log_level,
    expected_log_1,
    expected_log_2,
    expected_function_return,
):
    com_aux_init.logger = logging.Logger("ok")
    mock_channel = mocker.patch.object(
        com_aux_init.channel, "open", side_effect=side_effect_mock
    )
    with caplog.at_level(log_level):
        result_create_inst = com_aux_init._create_auxiliary_instance()
    assert result_create_inst is expected_function_return
    assert expected_log_1 in caplog.text
    assert expected_log_2 in caplog.text
    mock_channel.assert_called()


def test_delete_auxiliary_instance_false(mocker, com_aux_init, caplog):
    com_aux_init.logger = logging.Logger("ok")
    com_aux_init.channel = None
    with caplog.at_level(logging.INFO):
        result_create_inst = com_aux_init._delete_auxiliary_instance()
    assert result_create_inst is True
    assert "Delete auxiliary instance" in caplog.text
    assert "Unable to close channel communication" in caplog.text


@pytest.mark.parametrize(
    "side_effect_mock, expected_log, expected_function_return",
    [
        (None, "", True),
        (Exception, "encountered error while sending message 'None' to", False),
    ],
)
def test_run_command_valid(
    mocker,
    com_aux_init,
    caplog,
    side_effect_mock,
    expected_log,
    expected_function_return,
):
    com_aux_init.logger = logging.Logger("ok")
    mock_channel = mocker.patch.object(
        com_aux_init.channel, "cc_send", side_effect=side_effect_mock
    )
    with caplog.at_level(logging.INFO):
        result_create_inst = com_aux_init._run_command("send")
    assert result_create_inst is expected_function_return
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    "log_level, expected_log, expected_function_return, input_parameters",
    [
        (logging.WARNING, "received unknown command ", False, "return_test"),
        (logging.DEBUG, "ignored command ", True, "mock_msg"),
    ],
)
def test_run_command_notvalid(
    com_aux_init,
    caplog,
    log_level,
    expected_log,
    expected_function_return,
    input_parameters,
    request,
):

    com_aux_init.logger = logging.Logger("ok")
    input_parameters = request.getfixturevalue(input_parameters)

    with caplog.at_level(log_level):
        result_create_inst = com_aux_init._run_command(input_parameters)
        assert result_create_inst is expected_function_return
        assert expected_log + f"'{input_parameters} in {com_aux_init}'" in caplog.text


def test_receive_message_exception(mocker, com_aux_init, caplog):
    com_aux_init.logger = logging.Logger("ok")
    com_aux_init.channel = None
    with caplog.at_level(logging.ERROR):
        result_rec_msg = com_aux_init._receive_message(2)
    assert result_rec_msg is None
    assert (
        f"encountered error while receiving message via {com_aux_init.channel}"
        in caplog.text
    )


def test_receive_message_none(mocker, com_aux_init):
    mocker.patch.object(com_aux_init, "wait_and_get_report", return_value=None)
    recv = com_aux_init.receive_message(2)

    assert recv is None


def test_receive_message_with_remote_id(mocker, com_aux_init):
    ret = {"msg": b"\x01", "remote_id": 0x123}

    mocker.patch.object(com_aux_init, "wait_and_get_report", return_value=ret)
    recv = com_aux_init.receive_message(2)

    assert recv == (ret["msg"], ret["remote_id"])
