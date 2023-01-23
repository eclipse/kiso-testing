##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import multiprocessing
import threading

import pytest

from pykiso.connector import CChannel, Flasher


@pytest.fixture
def channel_obj(mocker):
    class TCChan(CChannel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")

    return TCChan


@pytest.fixture
def flasher_obj(tmp_file, mocker):
    class TFlash(Flasher):
        def __init__(self, *args, **kwargs):
            super(TFlash, self).__init__(*args, **kwargs)

        open = mocker.stub(name="open")
        close = mocker.stub(name="close")
        flash = mocker.stub(name="flash")

    return TFlash


def test_channel_constructor_thread(channel_obj):
    cc_inst = channel_obj(name="thread-channel")

    assert cc_inst.name == "thread-channel"
    assert isinstance(cc_inst._lock_tx, type(threading.RLock()))
    assert isinstance(cc_inst._lock_rx, type(threading.RLock()))
    assert isinstance(cc_inst._lock, type(threading.Lock()))


def test_channel_constructor_mp(channel_obj):

    cc_inst = channel_obj(processing=True, name="mp-channel")

    assert cc_inst.name == "mp-channel"
    assert isinstance(cc_inst._lock_tx, type(multiprocessing.RLock()))
    assert isinstance(cc_inst._lock_rx, type(multiprocessing.RLock()))
    assert isinstance(cc_inst._lock, type(multiprocessing.Lock()))


def test_channel_context_manager(channel_obj):
    cc_inst = channel_obj(name="thread-channel")

    with cc_inst as inst:
        pass

    cc_inst._cc_open.assert_called_once()
    cc_inst._cc_close.assert_called_once()


def test_channel_context_manager_exception(mocker, channel_obj):
    cc_inst = channel_obj(name="thread-channel")
    mocker.patch.object(cc_inst, "_cc_send", side_effect=ValueError)

    with pytest.raises(ValueError):
        with cc_inst as inst:
            inst.cc_send(msg=b"\x01\x02\x03")


def test_channel_cc_send(channel_obj):
    cc_inst = channel_obj(name="thread-channel")
    cc_inst.cc_send(msg=b"\x01\x02\x03")

    cc_inst._cc_send.assert_called_with(msg=b"\x01\x02\x03")


def test_channel_cc_send_raw(channel_obj, caplog):
    cc_inst = channel_obj(name="thread-channel")

    with caplog.at_level(logging.WARNING):
        cc_inst.cc_send(msg=b"\x01\x02\x03", raw=True)
    assert (
        "Use of 'raw' keyword argument is deprecated. It won't be passed to '_cc_send'."
        in caplog.text
    )

    cc_inst._cc_send.assert_called_with(msg=b"\x01\x02\x03", raw=True)


def test_channel_cc_receive(channel_obj):
    cc_inst = channel_obj(name="thread-channel")
    cc_inst.cc_receive()

    cc_inst._cc_receive.assert_called_with(timeout=0.1)


def test_channel_cc_receive_raw(channel_obj, caplog):
    cc_inst = channel_obj(name="thread-channel")

    with caplog.at_level(logging.WARNING):
        cc_inst.cc_receive(raw=True)
    assert (
        "Use of 'raw' keyword argument is deprecated. It won't be passed to '_cc_receive'."
        in caplog.text
    )
    cc_inst._cc_receive.assert_called_with(timeout=0.1, raw=True)


def test_channel_invalid_interface():
    with pytest.raises(TypeError):
        CChannel()


def test_flasher_constructor_binary_missing(flasher_obj):
    with pytest.raises(TypeError):
        flash_inst = flasher_obj(name="thread-channel")


def test_flasher_constructor_binary_path_invalid(flasher_obj):
    with pytest.raises(ValueError):
        flash_inst = flasher_obj(name="thread-channel", binary="super_bynary")


def test_flasher_context_manager(mocker, flasher_obj, tmp_file):
    flash_inst = flasher_obj(name="thread-channel", binary=tmp_file)

    with flash_inst as fl:
        pass

    flash_inst.open.assert_called_once()
    flash_inst.close.assert_called_once()


def test_flasher_context_manager_exception(mocker, flasher_obj, tmp_file):
    flash_inst = flasher_obj(name="thread-channel", binary=tmp_file)
    mocker.patch.object(flash_inst, "flash", side_effect=ValueError)

    with pytest.raises(ValueError):
        with flash_inst as fl:
            fl.flash()


def test_flasher_invalid_interface():
    with pytest.raises(TypeError):
        Flasher()
