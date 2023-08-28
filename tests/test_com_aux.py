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
    queue,
)
from pykiso.test_setup.dynamic_loader import DynamicImportLinker


@pytest.fixture
def com_aux_inst(cchannel_inst):
    return CommunicationAuxiliary(name="com_aux", com=cchannel_inst)


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

    com_aux.create_instance()
    msg = b"test"

    with com_aux.collect_messages():
        assert com_aux.send_message(msg)
        with caplog.at_level(logging.INTERNAL_DEBUG):
            rec_msg = com_aux.receive_message()

    assert rec_msg == msg
    assert com_aux.is_proxy_capable
    assert (
        f"retrieving message in {com_aux} (blocking={True}, timeout={None})"
        in caplog.text
    )
    com_aux.delete_instance()


def test_com_aux_send_message_without_contextmanager(mocker, caplog, com_aux_inst):
    com_aux_inst.create_instance()
    channel_cc_send_mock = mocker.patch.object(
        com_aux_inst.channel, "_cc_send", return_value=True
    )
    msg = b"test"

    com_aux_inst.send_message(msg)

    assert channel_cc_send_mock.call_args[1] == {"msg": b"test"}
    com_aux_inst.delete_instance()


def test_com_aux_receive_messaging_without_contextmanager(caplog, com_aux_inst, mocker):
    msg = {"id": 1, "msg": "test"}
    mocker.patch.object(com_aux_inst.channel, "_cc_receive", return_value=msg)

    com_aux_inst.create_instance()

    ret = com_aux_inst.receive_message()

    assert ret == msg["msg"]
    com_aux_inst.delete_instance()


def test_com_aux_receive_full_messaging_with_contextmanager(
    caplog, com_aux_inst, mocker
):
    msg = {"id": 1, "msg": "test"}
    mocker.patch.object(com_aux_inst.channel, "_cc_receive", return_value=msg)
    com_aux_inst.create_instance()

    with com_aux_inst.collect_messages():
        ret = com_aux_inst.receive_message()

    assert ret == msg["msg"]
    com_aux_inst.delete_instance()


def test_create_auxiliary_instance(com_aux_inst):
    state = com_aux_inst._create_auxiliary_instance()

    com_aux_inst.channel._cc_open.assert_called_once()
    assert state is True


def test_create_auxiliary_instance_exception(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst.channel, "open", side_effect=ValueError)

    state = com_aux_inst._create_auxiliary_instance()

    assert state is False


def test_delete_auxiliary_instance(com_aux_inst):
    state = com_aux_inst._delete_auxiliary_instance()

    com_aux_inst.channel._cc_close.assert_called_once()
    assert state is True


def test_delete_auxiliary_instance_exception(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst.channel, "close", side_effect=ValueError)

    state = com_aux_inst._delete_auxiliary_instance()

    assert state is False


def test_run_command_queue_tx_empty(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst, "_run_command", return_value=None)

    state = com_aux_inst.run_command(
        cmd_message="send", cmd_data=(None), blocking=False, timeout_in_s=0
    )

    assert state is None


def test__run_command_exception(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst.channel, "cc_send", side_effect=ValueError)

    com_aux_inst._run_command(cmd_message="send", cmd_data=b"\x01\x02\x03")
    cmd_state = com_aux_inst.queue_tx.get()

    assert cmd_state is False


def test__run_command_ignored_command(com_aux_inst):
    com_aux_inst._run_command(cmd_message=Message(), cmd_data=b"\x01\x02\x03")
    cmd_state = com_aux_inst.queue_tx.get()

    assert cmd_state is False


def test__run_command_unknown_command(com_aux_inst):
    com_aux_inst._run_command(cmd_message="super_command", cmd_data=b"\x01\x02\x03")
    cmd_state = com_aux_inst.queue_tx.get()

    assert cmd_state is False


def test_receive_message_with_remote_id(mocker, com_aux_inst):
    ret = {"msg": b"\x01", "remote_id": 0x123}

    com_aux_inst.queue_out.put(ret)
    recv = com_aux_inst.receive_message()

    assert recv == (ret["msg"], ret["remote_id"])


def test_receive_message_none(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst, "wait_for_queue_out", return_value=None)
    recv = com_aux_inst.receive_message()

    assert recv is None


def test__receive_message_exception(mocker, com_aux_inst):
    mocker.patch.object(com_aux_inst.channel, "cc_receive", side_effect=ValueError)

    com_aux_inst._receive_message(timeout_in_s=0)

    with pytest.raises(queue.Empty):
        com_aux_inst.queue_out.get_nowait()


def test_clear_buffer(com_aux_inst):
    com_aux_inst.queue_out.put(b"test")

    com_aux_inst.clear_buffer()

    assert com_aux_inst.queue_out.empty()
