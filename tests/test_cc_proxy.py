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
        msg = b"\x12\x34\x56"
        remote_id = 0x500
        proxy_inst._cc_send((msg, remote_id), raw=True)
        rc_msg = proxy_inst.queue_in.get()
        assert rc_msg[0][0] == b"\x12\x34\x56"
        assert rc_msg[0][1] == 0x500
        assert rc_msg[1] == True


@pytest.mark.parametrize(
    "timeout, raw, any_msg",  # any_msg contains ((message', 'source))
    [
        (0.200, True, (b"\x12\x34\x56", None)),
        (0, False, (b"\x12", 0x500)),
        (None, None, (None, None)),
    ],
)
def test_cc_receive(timeout, raw, any_msg):
    with CCProxy() as proxy_inst:
        proxy_inst.queue_out.put((any_msg, raw))
        msg = proxy_inst._cc_receive(timeout, raw)
        assert msg == any_msg


def test_cc_receive_timeout():
    with CCProxy() as proxy_inst:
        proxy_inst.timeout = 0.01
        msg = proxy_inst._cc_receive()
        assert msg == None
