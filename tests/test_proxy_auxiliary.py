##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import importlib
import logging
import queue
import sys
import threading

import pytest

from pykiso.lib.auxiliaries.proxy_auxiliary import (
    CCProxy,
    ConfigRegistry,
    DTAuxiliaryInterface,
    ProxyAuxiliary,
    log,
)

AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
AUX_LIST_INCOMPATIBLE = ["MockAux3"]
CHANNEL_LIST_INCOMPATIBLE = ["MockAux4"]


@pytest.fixture
def mock_auxiliaries(mocker, cchannel_inst):
    class MockProxyCChannel(CCProxy):
        def __init__(self, name=None, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.name = name
            self.queue_in = queue.Queue()
            self.queue_out = queue.Queue()

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")
        detach_tx_callback = mocker.stub(name="detach_tx_callback")
        attach_tx_callback = mocker.stub(name="attach_tx_callback")

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

    class MockAux4:
        def __init__(self, **kwargs):
            self.channel = cchannel_inst
            self.is_proxy_capable = True

    sys.modules["pykiso.auxiliaries.MockAux1"] = MockAux1()
    sys.modules["pykiso.auxiliaries.MockAux2"] = MockAux2()
    sys.modules["pykiso.auxiliaries.MockAux3"] = MockAux3()
    sys.modules["pykiso.auxiliaries.MockAux4"] = MockAux4()

    return MockProxyCChannel()


@pytest.fixture
def mock_aux_interface(mocker, mock_auxiliaries):
    class MockAuxInterface(DTAuxiliaryInterface):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            self.channel = mock_auxiliaries
            super().__init__(name="mp_aux")

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _create_auxiliary_instance.return_value = True
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _delete_auxiliary_instance.return_value = False
        _run_command = mocker.stub(name="_run_command")
        _receive_message = mocker.stub(name="_receive_message")

    sys.modules["pykiso.auxiliaries.MockAuxInterface"] = MockAuxInterface()

    return MockAuxInterface()


def test_constructor(mocker, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [])

    assert isinstance(proxy_inst.proxy_channels, tuple)
    assert len(proxy_inst.proxy_channels) == 0


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
    mock_check_aux = mocker.patch.object(ProxyAuxiliary, "_check_aux_compatibility")
    mock_check_channels = mocker.patch.object(
        ProxyAuxiliary, "_check_channels_compatibility"
    )
    mock_bind_channel = mocker.patch.object(CCProxy, "_bind_channel_info")

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES, mock_aux_interface])

    mock_check_channels.assert_called_once()
    assert mock_check_aux.call_count == len([*AUX_LIST_NAMES, mock_aux_interface])
    assert mock_bind_channel.call_count == len([*AUX_LIST_NAMES, mock_aux_interface])
    assert len(proxy_inst.proxy_channels) == 3
    assert all(isinstance(items, CCProxy) for items in proxy_inst.proxy_channels)


def test_get_proxy_con_invalid(mocker, caplog, cchannel_inst):

    mocker.patch.object(ConfigRegistry, "get_auxes_alias")

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, ["not_exist_aux", "fake_aux"])

    assert "Auxiliary 'not_exist_aux' doesn't exist" in caplog.text
    assert "Auxiliary 'fake_aux' doesn't exist" in caplog.text
    assert len(proxy_inst.proxy_channels) == 0


def test_auto_start_stop(cchannel_inst):
    class SomeAuxiliary(DTAuxiliaryInterface):
        def __init__(self, name="fake_aux"):
            self.channel = CCProxy()
            super().__init__(name, is_proxy_capable=True)

        def _create_auxiliary_instance(self):
            self.channel.open()
            return True

        def _delete_auxiliary_instance(self):
            self.channel.close()
            return True

        def _receive_message(self, timeout_in_s):
            pass

        def _run_command(self, cmd_message, cmd_data):
            pass

    aux1 = SomeAuxiliary("aux1")
    aux2 = SomeAuxiliary("aux2")
    cchannel_inst._cc_receive.return_value = {"msg": None}

    proxy_inst = ProxyAuxiliary(cchannel_inst, [aux1, aux2], name="proxy")
    assert proxy_inst._open_connections == 0
    assert proxy_inst.channel._cc_open.call_count == 0
    assert proxy_inst.channel._cc_close.call_count == 0
    assert proxy_inst.is_instance == False

    aux1.start()
    assert proxy_inst._open_connections == 1
    assert proxy_inst.channel._cc_open.call_count == 1
    assert proxy_inst.is_instance == True

    aux2.start()
    assert proxy_inst._open_connections == 2
    assert proxy_inst.channel._cc_open.call_count == 1
    assert proxy_inst.is_instance == True

    aux1.stop()
    assert proxy_inst._open_connections == 1
    assert proxy_inst.channel._cc_close.call_count == 0
    assert proxy_inst.is_instance == True

    aux2.stop()
    assert proxy_inst._open_connections == 0
    assert proxy_inst.channel._cc_close.call_count == 1
    assert proxy_inst.is_instance == False


def test_getattr_physical_cchannel(
    mocker, cchannel_inst, mock_aux_interface, mock_auxiliaries
):
    mocker.patch.object(ProxyAuxiliary, "_check_aux_compatibility")
    mocker.patch.object(ProxyAuxiliary, "_check_channels_compatibility")

    cchannel_inst.some_attribute = object()

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES, mock_aux_interface])
    proxy_inst.lock = mocker.MagicMock()

    mock_aux1 = importlib.import_module("pykiso.auxiliaries.MockAux1")

    assert isinstance(mock_aux1.channel, CCProxy)
    assert isinstance(proxy_inst.channel, type(cchannel_inst))

    assert mock_aux1.channel._physical_channel is cchannel_inst

    # attribute exists in the physical channel instance
    assert mock_aux1.channel.some_attribute is cchannel_inst.some_attribute
    proxy_inst.lock.__enter__.assert_called_once()
    proxy_inst.lock.__exit__.assert_called_once()
    proxy_inst.lock.reset_mock()

    # attribute exists in the proxy channel instance
    assert mock_aux1.channel.cc_send is not cchannel_inst.cc_send
    proxy_inst.lock.__enter__.assert_not_called()
    proxy_inst.lock.__exit__.assert_not_called()

    # attribute does not exist in physical channel
    with pytest.raises(AttributeError, match="has no attribute 'does_not_exist'"):
        mock_aux1.channel.does_not_exist
    proxy_inst.lock.__enter__.assert_called_once()
    proxy_inst.lock.__exit__.assert_called_once()

    # attribute does not exist in proxy channel (no physical channel attached)
    proxy_inst.lock.reset_mock()
    mock_aux1.channel._physical_channel = None
    with pytest.raises(AttributeError, match="has no attribute 'does_not_exist'"):
        mock_aux1.channel.does_not_exist
    proxy_inst.lock.__enter__.assert_not_called()
    proxy_inst.lock.__exit__.assert_not_called()


def test_get_proxy_con_pre_load(mocker, cchannel_inst):
    mocker.patch.object(ConfigRegistry, "get_auxes_alias", return_value="later_aux")
    mocker.patch.object(ProxyAuxiliary, "_check_channels_compatibility")
    mocker.patch.object(CCProxy, "_bind_channel_info")

    class Linker:
        def __init__(self):
            self._aux_cache = AuxCache()

    class FakeCCProxy:
        def _bind_channel_info(self, *args, **kwargs):
            pass

    class FakeAux:
        def __init__(self):
            self.channel = FakeCCProxy()
            self.is_proxy_capable = True

    class AuxCache:
        def get_instance(self, aux_name):
            return FakeAux()

    ConfigRegistry._linker = Linker()

    proxy_inst = ProxyAuxiliary(cchannel_inst, ["later_aux"])

    assert len(proxy_inst.proxy_channels) == 1
    assert isinstance(proxy_inst.proxy_channels[0], FakeCCProxy)


def test_check_aux_compatibility_exception(mocker, cchannel_inst):

    with pytest.raises(NotImplementedError):
        ProxyAuxiliary(cchannel_inst, [*AUX_LIST_INCOMPATIBLE])


def test_check_channels_compatibility_exception(mocker, cchannel_inst):

    with pytest.raises(TypeError):
        ProxyAuxiliary(cchannel_inst, [*CHANNEL_LIST_INCOMPATIBLE])


def test_create_auxiliary_instance(mocker, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    dispatch = mocker.patch.object(proxy_inst, "_dispatch_tx_method_to_channels")

    state = proxy_inst._create_auxiliary_instance()

    dispatch.assert_called_once()
    proxy_inst.channel._cc_open.assert_called_once()
    assert state is True


def test_create_auxiliary_instance_exception(mocker, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    mocker.patch.object(proxy_inst.channel, "_cc_open", side_effect=ValueError)

    state = proxy_inst._create_auxiliary_instance()

    assert state is False


def test_delete_auxiliary_instance(cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    state = proxy_inst._delete_auxiliary_instance()

    proxy_inst.channel._cc_close.assert_called_once()
    assert state is True


def test_delete_auxiliary_instance_exception(mocker, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    mocker.patch.object(proxy_inst.channel, "_cc_close", side_effect=ValueError)

    state = proxy_inst._delete_auxiliary_instance()

    assert state is False


@pytest.mark.parametrize(
    "response",
    [
        {"msg": b"\x12\x34\x56", "remote_id": 0x545},
        {"msg": b"\x12\x34\x56\x12\x34\x56", "remote_id": None},
    ],
)
def test_receive_message_valid(mocker, mock_auxiliaries, cchannel_inst, response):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    mocker.patch.object(proxy_inst.channel, "cc_receive", return_value=response)

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


def test_receive_message_no_message(mocker, mock_auxiliaries, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    mocker.patch.object(proxy_inst.channel, "cc_receive", return_value={"msg": None})

    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliaries.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliaries.MockAux2"]

    assert link_aux_1.channel.queue_out.empty()
    assert link_aux_2.channel.queue_out.empty()


def test_receive_message_exception(mocker, mock_auxiliaries, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    mocker.patch.object(proxy_inst.channel, "cc_receive", return_value=ValueError())

    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliaries.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliaries.MockAux2"]

    assert link_aux_1.channel.queue_out.empty()
    assert link_aux_2.channel.queue_out.empty()


def test_dispatch_tx_method_to_channels(cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    proxy_inst._dispatch_tx_method_to_channels()

    aux_1 = sys.modules["pykiso.auxiliaries.MockAux1"]
    aux_2 = sys.modules["pykiso.auxiliaries.MockAux2"]

    aux_1.channel.attach_tx_callback.assert_called()
    aux_2.channel.attach_tx_callback.assert_called()


@pytest.mark.parametrize(
    "req",
    [
        {"msg": b"\x12\x34\x56", "remote_id": 0x545},
        {"msg": b"\x12\x34", "remote_id": 0x001},
        {"msg": b"\x12\x34\x12\x34\x56", "remote_id": None},
    ],
)
def test_dispatch_command(mocker, mock_auxiliaries, cchannel_inst, req):
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


@pytest.mark.parametrize(
    "req",
    [
        {"msg": b"\x12\x34\x56", "remote_id": 0x545},
        {"msg": b"\x12\x34", "remote_id": 0x001},
        {"msg": b"\x12\x34\x12\x34\x56", "remote_id": None},
    ],
)
def test__run_command(mocker, cchannel_inst, req):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    dispatch = mocker.patch.object(proxy_inst, "_dispatch_command")

    conn_not_use = sys.modules["pykiso.auxiliaries.MockAux2"].channel

    proxy_inst._run_command(conn_not_use, **req)

    dispatch.assert_called_with(con_use=conn_not_use, **req)
    proxy_inst.channel._cc_send.assert_called()


def test_run_command(mocker, cchannel_inst):
    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    _run = mocker.patch.object(proxy_inst, "_run_command")

    conn_use = sys.modules["pykiso.auxiliaries.MockAux1"].channel
    req = {"msg": b"\x12\x34\x56", "remote_id": 0x545}
    proxy_inst.run_command(conn_use, **req)

    _run.assert_called_with(conn_use, **req)
