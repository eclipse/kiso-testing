##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import threading

import pytest

from pykiso import CChannel
from pykiso.lib.auxiliaries.instrument_control_auxiliary import (
    InstrumentControlAuxiliary,
)
from pykiso.lib.connectors.cc_visa import VISAChannel


@pytest.fixture
def aux_inst(mocker, cchannel_inst):
    return InstrumentControlAuxiliary(cchannel_inst, "Elektro-Automatik")


@pytest.fixture
def cc_visa_inst(mocker):
    class VisaChan(CChannel):
        def __init__(self, *args, **kwargs):
            super(VisaChan, self).__init__(*args, **kwargs)

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")
        query = mocker.stub(name="query")

    return VisaChan(name="visa-test-channel")


def test_instrument_constructor(aux_inst):

    assert aux_inst.instrument == "Elektro-Automatik"
    assert aux_inst.write_termination == "\n"


def test_write(mocker, aux_inst):
    handle_write_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_write", return_value=None
    )
    aux_inst.write("fake_command")

    handle_write_mock.assert_called_with("fake_command", None)


def test_read(mocker, aux_inst):
    handle_read_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_read", return_value=None
    )
    aux_inst.read()

    handle_read_mock.assert_called_once()


def test_query(mocker, aux_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value=None
    )
    aux_inst.query("fake_command")

    handle_query_mock.assert_called_with("fake_command")


def test_create_auxiliary_instance(mocker, aux_inst, cchannel_inst):
    handle_write_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_write", return_value=None
    )

    state = aux_inst._create_auxiliary_instance()

    handle_write_mock.assert_called_with(
        "SYST:LOCK ON", ("SYST:LOCK:OWN?", ["REMOTE", "ON", "1"])
    )
    cchannel_inst._cc_open.assert_called_once()
    assert state


def test_create_auxiliary_instance_with_output_channel(mocker, aux_inst, cchannel_inst):
    handle_write_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_write", return_value=None
    )

    aux_inst.output_channel = 1
    aux_inst.helpers.instrument = ""
    state = aux_inst._create_auxiliary_instance()

    handle_write_mock.assert_called_with(
        "INST:NSEL 1", ("INST:NSEL?", f"{aux_inst.output_channel}")
    )
    cchannel_inst._cc_open.assert_called_once()
    assert state


def test_delete_auxiliary_instance(aux_inst, cchannel_inst):
    state = aux_inst._delete_auxiliary_instance()

    cchannel_inst._cc_close.assert_called_once()

    assert state


def test_handle_write_without_validation(aux_inst, cchannel_inst):
    req = "SYST:LOCK ON"
    response = aux_inst.handle_write(req)

    cchannel_inst._cc_send.assert_called_with(msg="SYST:LOCK ON\n")
    assert response == "NO_VALIDATION"


def test_handle_write_with_validation(mocker, aux_inst, cchannel_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value="ON"
    )
    mocker.patch("time.sleep", return_value=None)

    req = "SYST:LOCK ON"
    validation = ("SYST:LOCK:OWN?", ["REMOTE", "ON", "1"])

    response = aux_inst.handle_write(req, validation)

    cchannel_inst._cc_send.assert_called_with(msg="SYST:LOCK ON\n")
    handle_query_mock.assert_called_with(validation[0])
    assert response == "SUCCESS"


def test_handle_write_no_response(mocker, aux_inst, cchannel_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value=""
    )
    mocker.patch("time.sleep", return_value=None)

    req = "SYST:LOCK ON"
    validation = ("SYST:LOCK:OWN?", ["REMOTE", "ON", "1"])

    response = aux_inst.handle_write(req, validation)

    assert response == "FAILURE"


def test_handle_write_with_value_tag(mocker, aux_inst, cchannel_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value="42.0"
    )
    mocker.patch("time.sleep", return_value=None)

    req = "SOURce:VOLTage 42.0"
    validation = ("SOURce:VOLTage?", "VALUE{42}")

    response = aux_inst.handle_write(req, validation)

    assert response == "SUCCESS"


def test_handle_write_with_value_tag_missmatch(mocker, aux_inst, cchannel_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value="42.1"
    )
    mocker.patch("time.sleep", return_value=None)

    req = "SOURce:VOLTage 42.0"
    validation = ("SOURce:VOLTage?", "VALUE{42}")

    response = aux_inst.handle_write(req, validation)

    assert response == "FAILURE"


def test_handle_write_missmatch_value(mocker, aux_inst, cchannel_inst):
    handle_query_mock = mocker.patch.object(
        InstrumentControlAuxiliary, "handle_query", return_value="42.1"
    )
    mocker.patch("time.sleep", return_value=None)

    req = "SOURce:VOLTage 42.0"
    validation = ("SOURce:VOLTage?", "42")

    response = aux_inst.handle_write(req, validation)

    assert response == "FAILURE"


def test_handle_read(aux_inst, cchannel_inst):
    cchannel_inst._cc_receive.return_value = b"data"

    read_data = aux_inst.handle_read()

    cchannel_inst._cc_receive.assert_called_with(timeout=0.1)
    assert read_data == b"data"


def test_handle_query(mocker, aux_inst, cchannel_inst):
    expected_return = b"data"
    cchannel_inst._cc_receive.return_value = expected_return
    mocker.patch("time.sleep", return_value=None)
    query = "SYST:LOCK:OWN?"

    query_result = aux_inst.handle_query(query)

    cchannel_inst._cc_send.assert_called_with(
        msg=f"{query}{aux_inst.write_termination}",
    )
    cchannel_inst._cc_receive.assert_called_with(timeout=0.1)
    assert query_result == expected_return.decode().strip()


def test_handle_query_with_visa_cc(mocker, aux_inst, cc_visa_inst):
    mocker.patch("time.sleep", return_value=None)
    query = "SYST:LOCK:OWN?"
    aux_inst.channel = cc_visa_inst
    aux_inst.handle_query(query)

    cc_visa_inst.query.assert_called_with(f"{query}{aux_inst.write_termination}")
