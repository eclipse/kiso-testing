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
import sys
from pathlib import Path

import pytest

from pykiso.connector import CChannel
from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.auxiliaries.mp_proxy_auxiliary import (
    ConfigRegistry,
    MpProxyAuxiliary,
    TraceOptions,
)


@pytest.fixture
def mock_auxiliaries(mocker):
    class MockProxyCChannel(CChannel):
        def __init__(self, name=None, *args, **kwargs):
            self.name = name
            self.queue_in = queue.Queue()
            self.queue_out = queue.Queue()
            super(MockProxyCChannel, self).__init__(*args, **kwargs)

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
    mock_check_comp = mocker.patch.object(MpProxyAuxiliary, "_check_compatibility")

    mock_get_alias = mocker.patch.object(
        ConfigRegistry, "get_auxes_alias", return_value="later_aux"
    )
    mp_proxy_auxiliary_inst.aux_list = ["later_aux"]

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

    with caplog.at_level(
        logging.WARNING,
    ):

        result_get_proxy = mp_proxy_auxiliary_inst.get_proxy_con(["later_aux"])
    assert (
        "Auxiliary : later_aux is not using import magic mechanism (pre-loaded)"
        in caplog.text
    )
    assert len(result_get_proxy) == 1
    assert isinstance(result_get_proxy[0], bool)
    mock_check_comp.assert_called()
    mock_get_alias.get_called()


def test_get_proxy_con_valid_(mocker, mp_proxy_auxiliary_inst, mock_auxiliaries):
    mock_check_comp = mocker.patch.object(MpProxyAuxiliary, "_check_compatibility")

    AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
    result_get_proxy = mp_proxy_auxiliary_inst.get_proxy_con(AUX_LIST_NAMES)

    assert len(result_get_proxy) == 2
    assert all(isinstance(items, CChannel) for items in result_get_proxy)
    mock_check_comp.assert_called()


def test_get_proxy_con_invalid_(mocker, caplog, mp_proxy_auxiliary_inst):
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


@pytest.mark.parametrize(
    "is_instance, request_value",
    [
        (False, "create_auxiliary_instance"),
        (True, "delete_auxiliary_instance"),
        (False, "Test"),
    ],
)
def test_run(
    mocker,
    mock_mp_proxy_aux,
    is_instance,
    request_value,
    caplog,
):
    mock_init_logger = mocker.patch.object(mock_mp_proxy_aux, "initialize_loggers")
    mock_mp_proxy_aux.logger = logging.getLogger(__name__)
    mock_event_init_trace = mocker.patch.object(mock_mp_proxy_aux, "_init_trace")
    mock_event_is_set = mocker.patch(
        "multiprocessing.synchronize.Event.is_set", side_effect=[False, True]
    )
    mock_queue_empty = mocker.patch.object(mock_mp_proxy_aux.queue_in, "empty")
    mock_queue_empty.return_value = False
    mock_queue_get_no_wait = mocker.patch.object(
        mock_mp_proxy_aux.queue_in, "get_nowait"
    )
    mock_queue_get_no_wait.return_value = request_value
    mock_mp_proxy_aux.is_instance = is_instance
    with caplog.at_level(logging.INFO):
        mock_mp_proxy_aux.run()
    mock_init_logger.assert_called()
    assert mock_event_is_set.call_count == 2
    mock_queue_empty.assert_called()
    mock_queue_get_no_wait.assert_called()
    mock_event_init_trace.assert_called()
    if request_value == "Test":
        assert f"Unknown request 'Test', will not be processed!" in caplog.text
        assert f"Aux status: {mock_mp_proxy_aux.__dict__}" in caplog.text
