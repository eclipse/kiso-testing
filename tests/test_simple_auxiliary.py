##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import pytest

from pykiso.interfaces.simple_auxiliary import (
    AuxiliaryInterface,
    SimpleAuxiliaryInterface,
)


class ConcreteSimpleAux(SimpleAuxiliaryInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _create_auxiliary_instance(self):
        pass

    def _delete_auxiliary_instance(self):
        pass


@pytest.fixture
def aux_instance(mocker):

    mocker.patch.object(ConcreteSimpleAux, "_create_auxiliary_instance")
    mocker.patch.object(ConcreteSimpleAux, "_delete_auxiliary_instance")

    return ConcreteSimpleAux(name="fake_aux")


def test_constructor(aux_instance):

    assert aux_instance.name == "fake_aux"
    assert not aux_instance.is_instance


def test_initialize_loggers(mocker):
    mock_log = mocker.patch.object(AuxiliaryInterface, "initialize_loggers")

    logger = [logging.getLogger(__name__)]
    SimpleAuxiliaryInterface.initialize_loggers(logger)
    mock_log.assert_called_with(logger)


def test_create_instance(mocker, aux_instance):
    mock_create = mocker.patch.object(
        ConcreteSimpleAux, "_create_auxiliary_instance", return_value=True
    )

    state = aux_instance.create_instance()

    mock_create.assert_called_once()
    assert aux_instance.is_instance
    assert state


def test_delete_instance(mocker, aux_instance):
    mock_delete = mocker.patch.object(
        ConcreteSimpleAux, "_delete_auxiliary_instance", return_value=True
    )

    state = aux_instance.delete_instance()

    mock_delete.assert_called_once()
    assert not aux_instance.is_instance
    assert state


def test_resume(mocker, aux_instance):
    mock_create = mocker.patch.object(
        ConcreteSimpleAux, "_create_auxiliary_instance", return_value=True
    )
    aux_instance.is_instance = False

    aux_instance.resume()

    mock_create.assert_called_once()
    assert aux_instance.is_instance


def test_resume_error(caplog, aux_instance):
    aux_instance.is_instance = True

    with caplog.at_level(logging.WARNING):
        aux_instance.resume()

    assert "is already running" in caplog.text


def test_suspend(mocker, aux_instance):
    mock_delete = mocker.patch.object(
        ConcreteSimpleAux, "_delete_auxiliary_instance", return_value=True
    )
    aux_instance.is_instance = True

    aux_instance.suspend()

    mock_delete.assert_called_once()
    assert not aux_instance.is_instance


def test_suspend_error(caplog, aux_instance):
    aux_instance.is_instance = False

    with caplog.at_level(logging.WARNING):
        aux_instance.suspend()

    assert "is already stopped" in caplog.text
