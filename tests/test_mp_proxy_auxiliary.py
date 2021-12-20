##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
from collections import namedtuple
from pathlib import Path

import pytest

from pykiso.lib.auxiliaries.mp_proxy_auxiliary import (
    MpProxyAuxiliary,
    TraceOptions,
)


def test_constructor(mocker, cchannel_inst):
    mock_start = mocker.patch.object(MpProxyAuxiliary, "start", return_value=None)

    proxy_inst = MpProxyAuxiliary(
        name="mp_aux",
        com=cchannel_inst,
        aux_list=[],
        activate_trace=True,
        trace_dir=Path(),
        trace_name="fake_trace",
    )

    assert proxy_inst.trace_options.activate
    assert isinstance(proxy_inst.trace_options, TraceOptions)
    assert proxy_inst.trace_options.dir == Path()
    assert proxy_inst.trace_options.name == "fake_trace"
    assert proxy_inst.logger is None
    assert isinstance(proxy_inst.proxy_channels, tuple)
    assert len(proxy_inst.proxy_channels) == 0
    mock_start.assert_called_once()


def test_run(mocker, cchannel_inst):
    mocker.patch.object(MpProxyAuxiliary, "start", return_value=None)
    mock_init_logger = mocker.patch.object(
        MpProxyAuxiliary, "initialize_loggers", return_value=None
    )
    mock_init_trace = mocker.patch.object(
        MpProxyAuxiliary, "_init_trace", return_value=None
    )

    proxy_inst = MpProxyAuxiliary(
        name="mp_aux",
        com=cchannel_inst,
        aux_list=[],
        activate_trace=True,
        trace_dir=Path(),
        trace_name="fake_trace",
    )
    proxy_inst.logger = logging.getLogger(__name__)
    proxy_inst.stop()
    proxy_inst.run()
    mock_init_trace.assert_called_once()
    mock_init_logger.assert_called_once()
