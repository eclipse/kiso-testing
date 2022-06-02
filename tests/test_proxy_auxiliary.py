# ##########################################################################
# # Copyright (c) 2010-2022 Robert Bosch GmbH
# # This program and the accompanying materials are made available under the
# # terms of the Eclipse Public License 2.0 which is available at
# # http://www.eclipse.org/legal/epl-2.0.
# #
# # SPDX-License-Identifier: EPL-2.0
# ##########################################################################

import logging
import queue
import sys
import threading

import pytest

from pykiso.connector import CChannel
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.auxiliaries.proxy_auxiliary import (
    ConfigRegistry,
    ProxyAuxiliary,
    log,
)

AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
AUX_LIST_INCOMPATIBLE = ["MockAux3"]


@pytest.fixture
def mock_auxiliaries(mocker):
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

    class MockAux1:
        def __init__(self, **kwargs):
            self.channel = MockProxyCChannel("test-cc-proxy")
            self.is_proxy_capable = True

    class MockAux2:
        def __init__(self, **kwargs):
            self.channel = MockProxyCChannel("test-cc-proxy")
            self.is_proxy_capable = True

    class MockAux3:
        def __init__(self, **kwargs):
            self.channel = MockProxyCChannel("test-cc-proxy")
            self.is_proxy_capable = False

    sys.modules["pykiso.auxiliaries.MockAux1"] = MockAux1()
    sys.modules["pykiso.auxiliaries.MockAux2"] = MockAux2()
    sys.modules["pykiso.auxiliaries.MockAux3"] = MockAux3()

    return MockProxyCChannel()


@pytest.fixture
def mock_aux_interface(mocker, mock_auxiliaries):
    class MockAuxInterface(AuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            self.channel = mock_auxiliaries
            super().__init__(
                name="mp_aux",
            )

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _create_auxiliary_instance.return_value = True
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _delete_auxiliary_instance.return_value = False
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")

    sys.modules["pykiso.auxiliaries.MockAuxInterface"] = MockAuxInterface()

    return MockAuxInterface()


def test_constructor(mocker, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [])

    assert isinstance(proxy_inst.proxy_channels, tuple)
    assert len(proxy_inst.proxy_channels) == 0


def test_auto_start_disable(mocker, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")
    mock_inst_creation = mocker.patch.object(ProxyAuxiliary, "create_instance")
    mock_start = mocker.patch.object(threading.Thread, "start")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [], auto_start=False)

    assert not proxy_inst.is_alive()

    proxy_inst.start()

    mock_inst_creation.assert_called_once()
    mock_start.assert_called_once()


def test_auto_start_already_running(mocker, cchannel_inst):
    mock_is_alive = mocker.patch.object(threading.Thread, "is_alive", return_value=True)

    proxy_inst = ProxyAuxiliary(cchannel_inst, [], auto_start=False)
    proxy_inst.start()

    mock_is_alive.assert_called_once()
    assert proxy_inst.is_instance is False


@pytest.mark.parametrize(
    "t_dir, t_name",
    [
        (None, None),
        (None, "mysuperlog"),
        ("", None),
        ("", "mysuperlog"),
    ],
)
def test_init_trace(mocker, t_dir, t_name):
    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)

    logger = ProxyAuxiliary._init_trace(True, t_dir, t_name)

    assert isinstance(logger, logging.Logger)
    assert logger.isEnabledFor(logging.DEBUG)
    assert logger == logging.getLogger(f"pykiso.lib.auxiliaries.proxy_auxiliary.PROXY")


def test_init_trace_not_activate(mocker):
    logger = ProxyAuxiliary._init_trace(activate=False)

    assert logger == log


def test_get_proxy_con_valid(mocker, cchannel_inst, mock_aux_interface):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(ProxyAuxiliary, "_check_compatibility")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES, mock_aux_interface])

    assert len(proxy_inst.proxy_channels) == 3
    assert all(isinstance(items, CChannel) for items in proxy_inst.proxy_channels)


def test_get_proxy_con_invalid(mocker, caplog, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")

    mocker.patch.object(ConfigRegistry, "get_auxes_alias")

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, ["not_exist_aux", "fake_aux"])

    assert "Auxiliary : not_exist_aux doesn't exist" in caplog.text
    assert "Auxiliary : fake_aux doesn't exist" in caplog.text
    assert len(proxy_inst.proxy_channels) == 0


def test_get_proxy_con_pre_load(mocker, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")

    mocker.patch.object(ConfigRegistry, "get_auxes_alias", return_value="later_aux")

    class Linker:
        def __init__(self):
            self._aux_cache = AuxCache()

    class FakeAux:
        def __init__(self):
            self.channel = True
            self.is_proxy_capable = True

    class AuxCache:
        def get_instance(self, aux_name):
            return FakeAux()

    ConfigRegistry._linker = Linker()

    proxy_inst = ProxyAuxiliary(cchannel_inst, ["later_aux"])

    assert len(proxy_inst.proxy_channels) == 1
    assert isinstance(proxy_inst.proxy_channels[0], bool)


def test_check_compatibility_exception(mocker, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")

    with pytest.raises(NotImplementedError):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_INCOMPATIBLE])


@pytest.mark.parametrize(
    "side_effect_value, stop_event_set, expected_function_return",
    [
        (None, False, True),
        (ValueError(), True, False),
    ],
)
def test_create_auxiliary_instance_valid(
    mocker, cchannel_inst, side_effect_value, stop_event_set, expected_function_return
):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(CChannel, "open", side_effect=side_effect_value)

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    state = proxy_inst._create_auxiliary_instance()

    assert state is expected_function_return
    assert proxy_inst.stop_event.is_set() is stop_event_set


@pytest.mark.parametrize(
    "side_effect_value, log_level, expected_log",
    [
        (None, logging.INFO, "Delete auxiliary instance"),
        (ValueError(), logging.ERROR, "Error encouting during channel closure"),
    ],
)
def test_delete_auxiliary_instance(
    mocker, caplog, cchannel_inst, side_effect_value, log_level, expected_log
):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(CChannel, "close", side_effect=side_effect_value)

    with caplog.at_level(log_level):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
        state = proxy_inst._delete_auxiliary_instance()

    assert expected_log in caplog.text
    assert state is True


def test_abort_command(mocker, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")
    proxy_inst = ProxyAuxiliary(cchannel_inst, [])
    ret_state = proxy_inst._abort_command()
    assert ret_state is True


@pytest.mark.parametrize(
    "response",
    [
        {"msg": b"\x12\x34\x56", "remote_id": 0x545},
        {"msg": b"\x12\x34\x56\x12\x34\x56", "remote_id": None},
    ],
)
def test_receive_message_valid(mocker, cchannel_inst, mock_auxiliaries, response):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(CChannel, "cc_receive", return_value=response)

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliaries.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliaries.MockAux2"]

    recv_aux1 = link_aux_1.channel.queue_out.get()
    recv_aux2 = link_aux_2.channel.queue_out.get()

    msg_1 = recv_aux1["msg"]
    source_1 = recv_aux1["remote_id"]
    msg_2 = recv_aux2["msg"]
    source_2 = recv_aux2["remote_id"]

    assert isinstance(recv_aux1, dict)
    assert isinstance(recv_aux2, dict)
    assert msg_1 == response["msg"]
    assert source_1 == response["remote_id"]
    assert msg_2 == response["msg"]
    assert source_2 == response["remote_id"]


def test_receive_message_no_message(mocker, cchannel_inst, mock_auxiliaries):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(CChannel, "cc_receive", return_value={"msg": None})

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliaries.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliaries.MockAux2"]

    assert link_aux_1.channel.queue_out.empty()
    assert link_aux_2.channel.queue_out.empty()


def test_receive_message_exception(mocker, caplog, cchannel_inst):
    mocker.patch.object(ProxyAuxiliary, "run")
    mocker.patch.object(CChannel, "cc_receive", side_effect=ValueError())

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
        proxy_inst._receive_message()

    assert "encountered error while receiving message via" in caplog.text


@pytest.mark.parametrize(
    "req",
    [
        {"msg": b"\x12\x34\x56", "remote_id": 0x545},
        {"msg": b"\x12\x34", "remote_id": 0x001},
        {"msg": b"\x12\x34\x12\x34\x56", "remote_id": None},
    ],
)
def test_dispatch_command(mocker, cchannel_inst, mock_auxiliaries, req):
    mocker.patch.object(ProxyAuxiliary, "run")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    conn_use = sys.modules["pykiso.auxiliaries.MockAux1"].channel
    conn_not_use = sys.modules["pykiso.auxiliaries.MockAux2"].channel

    proxy_inst._dispatch_command(conn_use, **req)

    spread_req = conn_not_use.queue_out.get()
    msg = spread_req["msg"]
    r_id = spread_req["remote_id"]

    assert conn_use.queue_out.empty()
    assert msg == req["msg"]
    assert r_id == req["remote_id"]


def test_run_command(mocker, cchannel_inst, mock_auxiliaries):
    mocker.patch.object(ProxyAuxiliary, "run")
    mock_dispatch = mocker.patch.object(ProxyAuxiliary, "_dispatch_command")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    conn_1 = sys.modules["pykiso.auxiliaries.MockAux2"].channel
    conn_2 = sys.modules["pykiso.auxiliaries.MockAux1"].channel

    command_1 = ((), {"msg": b"\x12\x34\x56", "remote_id": 0x512})
    command_2 = ((), {"msg": b"\x12", "remote_id": None})
    command_3 = ((), {"msg": b"\x12\x34\x56\x78", "remote_id": 0x56})

    conn_1.queue_in.put(command_1)
    conn_1.queue_in.put(command_2)
    conn_2.queue_in.put(command_3)

    proxy_inst._run_command()
    proxy_inst._run_command()

    mock_dispatch.assert_called()
    proxy_inst.channel._cc_send.assert_called_with(
        msg=command_2[1]["msg"], remote_id=command_2[1]["remote_id"]
    )


def test_run(mocker, cchannel_inst, mock_auxiliaries):
    mock_create = mocker.patch.object(
        ProxyAuxiliary, "_create_auxiliary_instance", return_value=True
    )
    mock_delete = mocker.patch.object(
        ProxyAuxiliary, "_delete_auxiliary_instance", return_value=True
    )
    mock_run_cmd = mocker.patch.object(ProxyAuxiliary, "_run_command")
    mock_recv = mocker.patch.object(ProxyAuxiliary, "_receive_message")

    # Start the Proxy's thread
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst.start()
    proxy_inst.create_instance()

    assert proxy_inst.is_instance is True
    mock_create.assert_called_once()

    proxy_inst.delete_instance()
    proxy_inst.stop()

    assert proxy_inst.is_instance is False
    mock_delete.assert_called_once()
    mock_run_cmd.assert_called()
    mock_recv.assert_called()
