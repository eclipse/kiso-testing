##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import multiprocessing
import queue

import pytest

from pykiso.lib.connectors.cc_proxy import CCProxy, Queue


def test_cc_open():
    with CCProxy() as proxy_inst:
        assert isinstance(proxy_inst.queue_in, type(Queue()))
        assert isinstance(proxy_inst.queue_out, type(Queue()))
        assert proxy_inst.timeout == 1


def test_cc_close():
    proxy_inst = CCProxy()
    proxy_inst._cc_open()
    proxy_inst.queue_in.put(b"\x01\x02")
    proxy_inst.queue_out.put(b"\x01\x02")
    proxy_inst._cc_close()

    assert isinstance(proxy_inst.queue_in, type(Queue()))
    assert isinstance(proxy_inst.queue_out, type(Queue()))
    assert proxy_inst.queue_in.empty()
    assert proxy_inst.queue_out.empty()


def test_cc_send():
    with CCProxy() as proxy_inst:
        proxy_inst._cc_send(b"\x12\x34\x56", raw=True, remote_id=0x500)
        arg, kwargs = proxy_inst.queue_in.get()
        assert arg[0] == b"\x12\x34\x56"
        assert kwargs["raw"] == True
        assert kwargs["remote_id"] == 0x500


@pytest.mark.parametrize(
    "timeout, raw, message, source",
    [
        (0.200, True, b"\x12\x34\x56", None),
        (0, False, b"\x12", 0x500),
        (None, None, None, None),
    ],
)
def test_cc_receive(timeout, raw, message, source):
    with CCProxy() as proxy_inst:
        proxy_inst.queue_out.put((message, source))
        msg, src = proxy_inst._cc_receive(timeout, raw)
        assert msg == message
        assert src == source


def test_cc_receive_timeout():
    with CCProxy() as proxy_inst:
        proxy_inst.timeout = 0.01
        msg, src = proxy_inst._cc_receive()
        assert msg == None
        assert src == None


def test_cc_share_with_remote_id():
    with CCProxy() as proxy_inst:
        proxy_inst.cc_share(msg=b"\x01\x0c", remote_id=0x123)
        msg, src = proxy_inst._cc_receive()

        assert msg == b"\x01\x0c"
        assert src == 0x123


def test_cc_share_with_positional():
    with CCProxy() as proxy_inst:
        proxy_inst.cc_share(b"\x01\x0c", 0x123)
        msg, src = proxy_inst._cc_receive()

        assert msg is None
        assert src is None


def test_cc_share_without_remote_id():
    with CCProxy() as proxy_inst:
        proxy_inst.cc_share(msg=b"\x01\x0c")
        msg, src = proxy_inst._cc_receive()

        assert msg == b"\x01\x0c"
        assert src is None
