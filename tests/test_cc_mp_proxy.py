##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import multiprocessing

import pytest

from pykiso.lib.connectors.cc_mp_proxy import CCMpProxy


def test_constructor():
    con_inst = CCMpProxy()

    assert isinstance(con_inst.queue_in, type(multiprocessing.Queue()))
    assert isinstance(con_inst.queue_out, type(multiprocessing.Queue()))


def test_queue_reference():
    con_inst = CCMpProxy()

    start_queue_in = con_inst.queue_in
    start_queue_out = con_inst.queue_out

    con_inst._cc_open()
    con_inst._cc_close()
    # check if the same references of both queue in/out is used
    assert con_inst.queue_in == start_queue_in
    assert con_inst.queue_out == start_queue_out
