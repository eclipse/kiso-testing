##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso import CChannel, Flasher


def test_cchan_abstract():
    """ensure CChannel is not instantiable"""
    with pytest.raises(TypeError):
        c = CChannel("will fail")


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
