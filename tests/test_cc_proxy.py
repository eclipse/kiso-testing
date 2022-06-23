##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.connectors.cc_proxy import CCProxy, queue


def test_constructor():
    proxy_inst = CCProxy()

    assert proxy_inst._tx_callback is None
    assert proxy_inst.queue_out is None
    assert proxy_inst.timeout == 1


def test_cc_open():
    with CCProxy() as proxy_inst:
        assert isinstance(proxy_inst.queue_out, queue.Queue)


def test_cc_close():
    proxy_inst = CCProxy()
    proxy_inst.open()
    old_out = proxy_inst.queue_out
    proxy_inst.close()

    assert proxy_inst.queue_out != old_out


def test_cc_send():
    def tx_func(con, *args, **kwargs):
        assert isinstance(con, CCProxy)
        assert args[0] == b"\x12\x34\x56"
        assert kwargs["raw"] == True
        assert kwargs["remote_id"] == 0x500

    with CCProxy() as proxy_inst:
        proxy_inst.attach_tx_callback(tx_func)
        proxy_inst._cc_send(b"\x12\x34\x56", raw=True, remote_id=0x500)


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


def test_detached_tx_callback():
    with CCProxy() as proxy_inst:
        proxy_inst._tx_callback = True
        proxy_inst.detach_tx_callback()
        assert proxy_inst._tx_callback is None


def test_attached_tx_callback():
    func = lambda x: x
    with CCProxy() as proxy_inst:
        proxy_inst.attach_tx_callback(func)
        assert proxy_inst._tx_callback == func


def test_attached_tx_callback_replace():
    func_1 = lambda x: x
    func_2 = lambda x: x + 1

    with CCProxy() as proxy_inst:
        proxy_inst.attach_tx_callback(func_1)
        assert proxy_inst._tx_callback == func_1
        proxy_inst.attach_tx_callback(func_2)
        assert proxy_inst._tx_callback != func_1
        assert proxy_inst._tx_callback == func_2
