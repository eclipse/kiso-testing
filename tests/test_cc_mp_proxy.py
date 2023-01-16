##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import pytest

from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy, multiprocessing, queue


def test_constructor():
    con_inst = CCMpProxy()

    assert isinstance(con_inst.queue_in, type(multiprocessing.Queue()))
    assert isinstance(con_inst.queue_out, type(multiprocessing.Queue()))

    # pickling quick test
    assert con_inst.__getstate__() == con_inst.__dict__
    new_dict = {**con_inst.__dict__, **{"some_attr": 12}}
    con_inst.__setstate__(new_dict)
    assert con_inst.__getstate__() == new_dict


def test_queue_reference():
    con_inst = CCMpProxy()

    start_queue_in = con_inst.queue_in
    start_queue_out = con_inst.queue_out

    con_inst._cc_open()
    con_inst._cc_close()
    # check if the same references of both queue in/out is used
    assert con_inst.queue_in == start_queue_in
    assert con_inst.queue_out == start_queue_out


def test_cc_send():
    with CCMpProxy() as proxy_inst:
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
    with CCMpProxy() as proxy_inst:
        proxy_inst.queue_out.put(raw_response)
        resp = proxy_inst._cc_receive(timeout, raw)

        assert resp["msg"] == raw_response["msg"]
        assert resp["remote_id"] == raw_response["remote_id"]


def test_cc_receive_timeout():
    with CCMpProxy() as proxy_inst:
        proxy_inst.timeout = 0.01
        response = proxy_inst._cc_receive()

        assert response["msg"] is None
        assert response.get("remote_id") is None
