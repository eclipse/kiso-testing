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
    "timeout, raw, raw_response",
    [
        (0.200, True, {"msg": b"\x12\x34\x56", "remote_id": None}),
        (0, False, {"msg": b"\x12", "remote_id": 0x500}),
        (None, None, {"msg": None, "remote_id": None}),
    ],
)
def test_cc_receive(timeout, raw, raw_response):
    with CCProxy() as proxy_inst:
        proxy_inst.queue_out.put(raw_response)
        resp = proxy_inst._cc_receive(timeout, raw)
        assert resp["msg"] == raw_response["msg"]
        assert resp["remote_id"] == raw_response["remote_id"]


def test_cc_receive_timeout():
    with CCProxy() as proxy_inst:
        proxy_inst.timeout = 0.01
        response = proxy_inst._cc_receive()
        assert response["msg"] is None
        assert response.get("remote_id") is None
