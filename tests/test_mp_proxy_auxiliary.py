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
from pathlib import Path

import pytest

import pykiso
from pykiso.connector import CChannel
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.auxiliaries.mp_proxy_auxiliary import (
    ConfigRegistry,
    MpProxyAuxiliary,
    TraceOptions,
)
from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy
from pykiso.lib.connectors.cc_proxy import CCProxy

pykiso.logging_initializer.log_options = pykiso.logging_initializer.LogOptions(
    ".", "INFO", "TEXT", False
)


@pytest.fixture
def mock_auxiliaries(mocker):
    class MockProxyCChannel(CCMpProxy):
        def __init__(self, name=None, *args, **kwargs):
            super(MockProxyCChannel, self).__init__(*args, **kwargs)
            self.name = name
            self.queue_out = queue.Queue()
            self.queue_in = queue.Queue()

        _cc_open = mocker.stub(name="_cc_open")
        open = mocker.stub(name="open")
        close = mocker.stub(name="close")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")
        cc_receive = mocker.stub(name="cc_receive")

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
    return (
        MockAux3(),
        MockProxyCChannel("test-cc-proxy"),
        MockProxyCChannel("test-channel"),
    )


@pytest.fixture
def mp_proxy_auxiliary_inst(mock_auxiliaries):
    proxy_inst = MpProxyAuxiliary(
        name="mp_aux",
        com=mock_auxiliaries[1],
        aux_list=[],
        activate_trace=True,
        trace_dir=Path(),
        trace_name="fake_trace",
    )
    proxy_inst.logger = logging.getLogger(__name__)
    return proxy_inst


@pytest.fixture
def mock_mp_proxy_aux(mocker, cchannel_inst):
    class access_static_method(MpProxyAuxiliary):
        def __init__(self, param_1=None, param_2=None, **kwargs):
            self.param_1 = param_1
            self.param_2 = param_2
            super().__init__(
                name="mp_aux",
                com=cchannel_inst,
                aux_list=[],
                activate_trace=True,
                trace_dir=Path(),
                trace_name="fake_trace",
            )

        def check_compatibility(self, aux: AuxiliaryInterface):
            access_static_method._check_compatibility(aux)

        def empty_queue(self, queue: queue.Queue):
            access_static_method._empty_queue(queue)

        def run(self):
            super().run()

        _create_auxiliary_instance = mocker.stub(name="_create_auxiliary_instance")
        _create_auxiliary_instance.return_value = True
        _delete_auxiliary_instance = mocker.stub(name="_delete_auxiliary_instance")
        _delete_auxiliary_instance.return_value = False
        _run_command = mocker.stub(name="_run_command")
        _abort_command = mocker.stub(name="_abort_command")
        _receive_message = mocker.stub(name="_receive_message")

    return access_static_method()


def test_constructor(mp_proxy_auxiliary_inst):
    proxy_inst = mp_proxy_auxiliary_inst
    assert proxy_inst.trace_options.activate
    assert isinstance(proxy_inst.trace_options, TraceOptions)
    assert proxy_inst.trace_options.dir == Path()
    assert proxy_inst.trace_options.name == "fake_trace"
    assert isinstance(proxy_inst.logger, logging.Logger)
    assert isinstance(proxy_inst.proxy_channels, tuple)
    assert len(proxy_inst.proxy_channels) == 0


def test_run(mocker, mp_proxy_auxiliary_inst):
    mocker.patch.object(MpProxyAuxiliary, "start", return_value=None)
    mock_init_logger = mocker.patch.object(
        MpProxyAuxiliary, "initialize_loggers", return_value=None
    )
    mock_init_trace = mocker.patch.object(
        MpProxyAuxiliary, "_init_trace", return_value=None
    )

    proxy_inst = mp_proxy_auxiliary_inst
    proxy_inst.logger = logging.getLogger(__name__)
    proxy_inst.stop()
    proxy_inst.run()
    mock_init_trace.assert_called_once()
    mock_init_logger.assert_called_once()


def test_init_trace(mocker, mp_proxy_auxiliary_inst, caplog):
    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)
    mock_formatter = mocker.patch("logging.Formatter")
    log = logging.getLogger(__name__)
    with caplog.at_level(
        logging.INFO,
    ):
        mp_proxy_auxiliary_inst._init_trace(log, True)
    assert "create proxy trace file at " in caplog.text
    mock_formatter.assert_called()


def test_init_trace_not_activated(mocker, mp_proxy_auxiliary_inst):
    result = mp_proxy_auxiliary_inst._init_trace(mp_proxy_auxiliary_inst.logger, False)
    assert result is None


def test_get_proxy_con_pre_load(mocker, mp_proxy_auxiliary_inst, caplog):
    mock_check_comp = mocker.patch.object(
        MpProxyAuxiliary, "_check_channels_compatibility"
    )

    mock_get_alias = mocker.patch.object(
        ConfigRegistry, "get_auxes_alias", return_value="later_aux"
    )
    mp_proxy_auxiliary_inst.aux_list = ["later_aux"]

    class Linker:
        def __init__(self):
            self._aux_cache = AuxCache()

    class FakeCCMpProxy(CCMpProxy):
        def _bind_channel_info(self, *args, **kwargs):
            pass

    class FakeAux:
        def __init__(self):
            self.channel = FakeCCMpProxy()
            self.is_proxy_capable = True

    class AuxCache:
        def get_instance(self, aux_name):
            return FakeAux()

    ConfigRegistry._linker = Linker()

    with caplog.at_level(logging.WARNING):
        result_get_proxy = mp_proxy_auxiliary_inst.get_proxy_con(["later_aux"])

    assert (
        "Auxiliary : later_aux is not using import magic mechanism (pre-loaded)"
        in caplog.text
    )
    assert len(result_get_proxy) == 1
    assert isinstance(result_get_proxy[0], FakeCCMpProxy)
    mock_check_comp.assert_called()
    mock_get_alias.get_called()


def test_get_proxy_con_valid(mocker, mp_proxy_auxiliary_inst, mock_auxiliaries):
    mock_check_comp = mocker.patch.object(MpProxyAuxiliary, "_check_compatibility")
    mock_check_channel_comp = mocker.patch.object(
        MpProxyAuxiliary, "_check_channels_compatibility"
    )

    AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
    result_get_proxy = mp_proxy_auxiliary_inst.get_proxy_con(AUX_LIST_NAMES)

    assert len(result_get_proxy) == len(AUX_LIST_NAMES)
    assert all(isinstance(items, CChannel) for items in result_get_proxy)
    mock_check_channel_comp.assert_called_once()
    assert mock_check_comp.call_count == len(AUX_LIST_NAMES)


def test_get_proxy_con_invalid_cchannel(mocker, caplog, mp_proxy_auxiliary_inst):
    mock_get_alias = mocker.patch.object(
        ConfigRegistry, "get_auxes_alias", return_value="later_aux"
    )
    mp_proxy_auxiliary_inst.aux_list = ["later_aux"]

    class Linker:
        def __init__(self):
            self._aux_cache = AuxCache()

    class OtherCChannel(CChannel):
        def _bind_channel_info(self, *args, **kwargs):
            pass

    class FakeAux:
        def __init__(self):
            self.channel = OtherCChannel()
            self.is_proxy_capable = True

    class AuxCache:
        def get_instance(self, aux_name):
            return FakeAux()

    ConfigRegistry._linker = Linker()

    with pytest.raises(TypeError):
        mp_proxy_auxiliary_inst.get_proxy_con(["later_aux"])


def test_get_proxy_con_invalid_aux(mocker, caplog, mp_proxy_auxiliary_inst):
    mock_get_alias = mocker.patch.object(
        ConfigRegistry, "get_auxes_alias", return_value="later_aux"
    )

    with caplog.at_level(logging.ERROR):
        result_get_proxy = mp_proxy_auxiliary_inst.get_proxy_con(
            ["not_exist_aux", "fake_aux"]
        )

    assert "Auxiliary : not_exist_aux doesn't exist" in caplog.text
    assert "Auxiliary : fake_aux doesn't exist" in caplog.text
    assert len(result_get_proxy) == 0

    mock_get_alias.assert_called()


def test_getattr_physical_cchannel(
    mocker, cchannel_inst, mp_proxy_auxiliary_inst, mock_auxiliaries
):
    mocker.patch.object(MpProxyAuxiliary, "_check_compatibility")
    mocker.patch.object(MpProxyAuxiliary, "_check_channels_compatibility")

    cchannel_inst.some_attribute = object()

    AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
    proxy_inst = MpProxyAuxiliary(cchannel_inst, AUX_LIST_NAMES, name="aux")
    proxy_inst.lock = mocker.MagicMock()

    mock_aux1 = importlib.import_module("pykiso.auxiliaries.MockAux1")

    assert isinstance(proxy_inst.channel, type(cchannel_inst))

    assert mock_aux1.channel._physical_channel is cchannel_inst

    # attribute exists in the physical channel
    assert mock_aux1.channel.some_attribute is cchannel_inst.some_attribute
    proxy_inst.lock.__enter__.assert_called_once()
    proxy_inst.lock.__exit__.assert_called_once()
    proxy_inst.lock.reset_mock()

    # attribute exists in the proxy channel
    assert mock_aux1.channel.cc_send is not cchannel_inst.cc_send
    proxy_inst.lock.__enter__.assert_not_called()
    proxy_inst.lock.__exit__.assert_not_called()

    # attribute does not exist in physical channel
    with pytest.raises(
        AttributeError, match="object has no attribute 'does_not_exist'"
    ):
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


def test_create_auxiliary_instance(mp_proxy_auxiliary_inst, caplog):

    with caplog.at_level(logging.INFO):
        result_create_inst = mp_proxy_auxiliary_inst._create_auxiliary_instance()
    assert result_create_inst is True
    assert "Create auxiliary instance" in caplog.text
    assert "Enable channel" in caplog.text


def test_create_auxiliary_instance_exception(mp_proxy_auxiliary_inst, caplog):
    mp_proxy_auxiliary_inst.channel = None
    with caplog.at_level(logging.ERROR):
        result_create_inst = mp_proxy_auxiliary_inst._create_auxiliary_instance()
    assert result_create_inst is False
    assert "Error encouting during channel creation" in caplog.text


def test_delete_auxiliary_instance(
    mocker, mp_proxy_auxiliary_inst, mock_auxiliaries, caplog
):
    mock_empty_queue = mocker.patch.object(MpProxyAuxiliary, "_empty_queue")
    mp_proxy_auxiliary_inst.proxy_channels = [mock_auxiliaries[1], mock_auxiliaries[2]]

    with caplog.at_level(logging.INFO):

        result = mp_proxy_auxiliary_inst._delete_auxiliary_instance()
    assert "Delete auxiliary instance" in caplog.text
    assert result is True
    mock_empty_queue.assert_called()
    assert mock_empty_queue.call_count == 5


def test_delete_instance_exception(mp_proxy_auxiliary_inst, caplog):
    mp_proxy_auxiliary_inst.channel = None
    with caplog.at_level(logging.ERROR):
        result = mp_proxy_auxiliary_inst._delete_auxiliary_instance()
    assert "Error encouting during channel closure" in caplog.text
    assert result is True


def test_receive_message(mp_proxy_auxiliary_inst, mock_auxiliaries, caplog):
    proxy_channel_test = mock_auxiliaries[1]
    proxy_channel_test.cc_receive.return_value = {
        "msg": b"340",
        "remote_id": "Test_source",
    }
    mp_proxy_auxiliary_inst.proxy_channels = [proxy_channel_test]
    with caplog.at_level(logging.DEBUG):
        result_rec_message = mp_proxy_auxiliary_inst._receive_message(1)
    assert (
        f"raw data : {b'340'.hex()} || channel : {mp_proxy_auxiliary_inst.channel.name}"
        in caplog.text
    )
    assert result_rec_message is None
    assert proxy_channel_test.queue_out.get_nowait() == {
        "msg": b"340",
        "remote_id": "Test_source",
    }


def test_receive_message_exception(mp_proxy_auxiliary_inst, mock_auxiliaries, caplog):
    proxy_channel_test = mock_auxiliaries[1]
    proxy_channel_test.cc_receive.return_value = "Tree", "test"
    mp_proxy_auxiliary_inst.proxy_channels = [proxy_channel_test]
    with caplog.at_level(logging.ERROR):
        result_rec_message = mp_proxy_auxiliary_inst._receive_message(1)

    assert (
        f"encountered error while receiving message via {mp_proxy_auxiliary_inst.channel}"
        in caplog.text
    )
    assert result_rec_message is None
    assert proxy_channel_test.queue_out.empty()


def test_dispatch_command_valid(mocker, mp_proxy_auxiliary_inst, mock_auxiliaries):
    proxy_channel_test = mock_auxiliaries[1]
    mp_proxy_auxiliary_inst.proxy_channels = [proxy_channel_test]
    compare_channel = mock_auxiliaries[2]
    result_rec_message = mp_proxy_auxiliary_inst._dispatch_command(
        compare_channel, **{"msg": b"340", "remote_id": 35}
    )
    assert result_rec_message is None
    assert proxy_channel_test.queue_out.get_nowait() == {"msg": b"340", "remote_id": 35}


def test_dispatch_command_invalid(mp_proxy_auxiliary_inst, mock_auxiliaries):
    proxy_channel_test = mock_auxiliaries[1]
    mp_proxy_auxiliary_inst.proxy_channels = [proxy_channel_test]
    result_rec_message = mp_proxy_auxiliary_inst._dispatch_command(
        proxy_channel_test, **{"msg": b"340", "remote_id": 35}
    )
    assert result_rec_message is None
    assert proxy_channel_test.queue_out.empty()


def test_run_command(mocker, mp_proxy_auxiliary_inst, mock_auxiliaries):
    mock_dispatch_command = mocker.patch.object(MpProxyAuxiliary, "_dispatch_command")
    mocker.patch.object(MpProxyAuxiliary, "_check_compatibility")
    mocker.patch.object(MpProxyAuxiliary, "_check_channels_compatibility")
    mocker.patch.object(mp_proxy_auxiliary_inst, "channel")
    mock_queue_empty = mocker.patch("queue.Queue.empty", return_value=False)
    mock_queue_get = mocker.patch(
        "queue.Queue.get", return_value=((False, "ok"), {"msg": "Test"})
    )

    AUX_LIST_NAMES = ["MockAux1"]
    mp_proxy_auxiliary_inst.proxy_channels = mp_proxy_auxiliary_inst.get_proxy_con(
        AUX_LIST_NAMES
    )

    assert len(mp_proxy_auxiliary_inst.proxy_channels) == 1

    result = mp_proxy_auxiliary_inst._run_command()

    assert result is None
    mock_dispatch_command.assert_called()
    mock_queue_empty.assert_called()
    mock_queue_get.assert_called()


def test_check_compatibility(mock_auxiliaries, mock_mp_proxy_aux):
    with pytest.raises(NotImplementedError):
        assert mock_auxiliaries[0].is_proxy_capable is False
        mock_mp_proxy_aux.check_compatibility(mock_auxiliaries[0])


def test_empty_queue(mocker, mock_mp_proxy_aux):
    spy_empty = mocker.spy(queue.Queue, "empty")
    spy_get = mocker.spy(queue.Queue, "get")
    queue_test = queue.Queue()
    queue_test.put("A")
    queue_test.put("AA")
    assert queue_test.qsize() == 2
    mock_mp_proxy_aux.empty_queue(queue_test)
    assert spy_empty.call_count == 3
    assert spy_get.call_count == 2


def test_run_create_auxiliary_instance_command(mocker, mp_proxy_auxiliary_inst):
    mock_logger = mocker.patch.object(mp_proxy_auxiliary_inst, "initialize_loggers")
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_empty = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in, "empty", return_value=False
    )
    mock_wait = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in,
        "get_nowait",
        return_value="create_auxiliary_instance",
    )
    mock_create = mocker.patch.object(
        mp_proxy_auxiliary_inst, "_create_auxiliary_instance", return_value=True
    )
    mock_put = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_out, "put", side_effect=ValueError
    )

    with pytest.raises(ValueError):
        mp_proxy_auxiliary_inst.run()
        mock_logger.assert_called_once()
        mock_trace.assert_called_once()
        mock_create.assert_called_once()
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_delete_auxiliary_instance_command(mocker, mp_proxy_auxiliary_inst):
    mp_proxy_auxiliary_inst.is_instance = True
    mock_logger = mocker.patch.object(mp_proxy_auxiliary_inst, "initialize_loggers")
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_empty = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in, "empty", return_value=False
    )
    mock_wait = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in,
        "get_nowait",
        return_value="delete_auxiliary_instance",
    )
    mock_delete = mocker.patch.object(
        mp_proxy_auxiliary_inst, "_delete_auxiliary_instance", return_value=True
    )
    mock_put = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_out, "put", side_effect=ValueError
    )

    with pytest.raises(ValueError):
        mp_proxy_auxiliary_inst.run()
        mock_logger.assert_called_once()
        mock_trace.assert_called_once()
        mock_delete.assert_called_once()
        mock_wait.assert_called_once()
        mock_put.assert_called_with(True)


def test_run_unknown_command(mocker, mp_proxy_auxiliary_inst):
    mp_proxy_auxiliary_inst.is_instance = True
    mp_proxy_auxiliary_inst.initialize_loggers()
    mock_empty = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in, "empty", return_value=False
    )
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_wait = mocker.patch.object(
        mp_proxy_auxiliary_inst.queue_in,
        "get_nowait",
        return_value=("fake_coammnd", "supr_command", 1),
    )
    mock_warning = mocker.patch.object(
        mp_proxy_auxiliary_inst.logger, "warning", side_effect=ValueError
    )

    with pytest.raises(ValueError):
        mp_proxy_auxiliary_inst.run()
        mock_warning.assert_called_once()
        mock_trace.assert_called_once()
        mock_wait.assert_called_once()


def test_run_receive_message(mocker, mp_proxy_auxiliary_inst):
    mp_proxy_auxiliary_inst.is_instance = True
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_cmd = mocker.patch.object(mp_proxy_auxiliary_inst, "_run_command")
    mock_recv = mocker.patch.object(
        mp_proxy_auxiliary_inst, "_receive_message", side_effect=ValueError
    )

    with pytest.raises(ValueError):
        mp_proxy_auxiliary_inst.run()
        mock_recv.assert_called_with(timeout_in_s=0)
        mock_cmd.assert_called_once()


def test_run_free_cpu_usage(mocker, mp_proxy_auxiliary_inst):
    mock_sleep = mocker.patch("time.sleep", side_effect=ValueError)
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")

    with pytest.raises(ValueError):
        mp_proxy_auxiliary_inst.run()
        mock_sleep.assert_called_with(0.050)


def test_run_stop_command_running_instance(mocker, mp_proxy_auxiliary_inst):
    mp_proxy_auxiliary_inst.is_instance = True
    mock_set = mocker.patch.object(
        mp_proxy_auxiliary_inst.stop_event, "is_set", return_value=True
    )
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_delete = mocker.patch.object(
        mp_proxy_auxiliary_inst, "_delete_auxiliary_instance", return_value=True
    )

    mp_proxy_auxiliary_inst.run()

    mock_delete.assert_called_once()
    mock_set.assert_called_once()


def test_run_stop_command_not_running_instance(mocker, mp_proxy_auxiliary_inst):
    mp_proxy_auxiliary_inst.is_instance = False
    mock_set = mocker.patch.object(
        mp_proxy_auxiliary_inst.stop_event, "is_set", return_value=True
    )
    mock_trace = mocker.patch.object(mp_proxy_auxiliary_inst, "_init_trace")
    mock_delete = mocker.patch.object(
        mp_proxy_auxiliary_inst, "_delete_auxiliary_instance"
    )

    mp_proxy_auxiliary_inst.run()

    mock_delete.assert_not_called()
    mock_set.assert_called_once()
