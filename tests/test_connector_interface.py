##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso import CChannel, Flasher


@pytest.fixture
def rlock_mock(mocker):
    class R_lock_dict:
        def __init__(self):
            self.att = None

        def acquire(self, Bool: bool):
            return False

        def release(self):
            return None

        def exists(self):
            return False

        def is_file(self):
            return False

    return R_lock_dict()


def test_connector_exit(mocker, cchannel_inst):
    mock_close = mocker.patch.object(CChannel, "close")
    with pytest.raises(TypeError):
        cchannel_inst.__exit__("test", TypeError, "TEST")

    mock_close.assert_called()


def test_cchan_abstract():
    """ensure CChannel is not instantiable"""
    with pytest.raises(TypeError):
        c = CChannel("will fail")


def test_cchan_interface(cchannel_inst, mocker):
    tracer = mocker.MagicMock()
    tracer.attach_mock(cchannel_inst._cc_open, "_cc_open")
    tracer.attach_mock(cchannel_inst._cc_close, "_cc_close")
    tracer.attach_mock(cchannel_inst._cc_receive, "_cc_receive")
    tracer.attach_mock(cchannel_inst._cc_send, "_cc_send")
    with cchannel_inst as ch:
        ch.cc_send("test", 0)
        ch.cc_receive(0)
    expected_calls = [
        mocker.call._cc_open(),
        mocker.call._cc_send(msg="test", raw=False),
        mocker.call._cc_receive(timeout=0, raw=False),
        mocker.call._cc_close(),
    ]
    print(repr(expected_calls))
    assert expected_calls == tracer.mock_calls


def test_cchannel_open_failed(mocker, cchannel_inst, rlock_mock):
    mocker.patch.object(cchannel_inst, "_lock", rlock_mock)
    with pytest.raises(ConnectionRefusedError):
        cchannel_inst.open()


def test_cchannel_cc_send_failed(mocker, cchannel_inst, rlock_mock, mock_msg):
    mocker.patch.object(cchannel_inst, "_lock", rlock_mock)
    with pytest.raises(ConnectionRefusedError):
        cchannel_inst.cc_send(mock_msg)


def test_cchannel_cc_receive_failed(mocker, cchannel_inst, rlock_mock):
    mock_acquire = mocker.patch.object(cchannel_inst, "_lock", rlock_mock)
    with pytest.raises(ConnectionRefusedError):
        receive_msg = cchannel_inst.cc_receive()
        mock_acquire.assert_called()
        assert receive_msg is None


def test_flash_abstract():
    """ensure Flasher is not instantiable"""
    with pytest.raises(TypeError):
        f = Flasher("will fail")


def test_flasher_interface(flasher_inst, mocker):
    tracer = mocker.MagicMock()
    tracer.attach_mock(flasher_inst.open, "open")
    tracer.attach_mock(flasher_inst.close, "close")
    tracer.attach_mock(flasher_inst.flash, "flash")
    with flasher_inst as fl:
        fl.flash()
    assert tracer.mock_calls == [
        mocker.call.open(),
        mocker.call.flash(),
        mocker.call.close(),
    ]


def test_flasher_init_failed_type_error(mocker, request):
    class Mock_flasher(Flasher):
        def __init__(self, binary, **kwargs):
            super().__init__(binary, **kwargs)

        flash = mocker.stub(name="flash")
        open = mocker.stub(name="open")
        close = mocker.stub(name="close")

    with pytest.raises(TypeError) as error:
        Mock_flasher(None)

    assert str(error.value) == "'binary' must be a path-like object, not None"


def test_flasher_init_failed_value_error(mocker, rlock_mock):
    class Mock_flasher(Flasher):
        def __init__(self, binary, **kwargs):
            super().__init__(binary, **kwargs)

        flash = mocker.stub(name="flash")
        open = mocker.stub(name="open")
        close = mocker.stub(name="close")

    mocker_resolve = mocker.patch("pathlib.Path.resolve", return_value=rlock_mock)

    with pytest.raises(ValueError) as error:
        Mock_flasher("test")
        mocker_resolve.assert_called()
    assert (
        str(error.value)
        == f"'binary' must be a path-like object to an existing file (got {rlock_mock})"
    )
