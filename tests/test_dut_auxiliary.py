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

from pykiso.interfaces.thread_auxiliary import AuxiliaryInterface
from pykiso.lib.auxiliaries.dut_auxiliary import DUTAuxiliary
from pykiso.lib.connectors.cc_rtt_segger import CCRttSegger
from pykiso.message import Message, MessageType
from pykiso.types import MsgType


class MockCChanel:
    def __init__(self, msg: Message = None):
        self.msg = msg

    def open(self):
        pass

    def close(self):
        pass

    def _cc_open(self):
        pass

    def _cc_close(self):
        pass

    def _cc_send(self, msg: MsgType, raw: bool = False):
        pass

    def _cc_receive(self, timeout: float = 0.1, raw: bool = False):
        return {"msg": self.msg}

    def cc_send(self, msg: MsgType, raw: bool = False):
        pass

    def cc_receive(self, timeout: float = 0.1, raw: bool = False):
        return {"msg": self.msg}


class MockFlasher:
    def __init__(self, is_flashed=True):
        self.is_flashed = is_flashed

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, typ, value, traceback):
        self.close()
        if value is not None:
            raise value

    def open(self):
        if not self.is_flashed:
            raise Exception("An exception occurred in open method")
        else:
            pass

    def close(self):
        pass

    def flash(self):
        if not self.is_flashed:
            raise Exception("An exception occurred in close method")
        else:
            pass


def test_dut_auxiliary_init(mocker):
    """Test the constructor with the connector and the flasher"""
    com = MockCChanel()
    flash = MockFlasher()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com, flash)

    assert not auxiliary.is_proxy_capable
    assert auxiliary.channel == com
    assert auxiliary.flash == flash
    assert not auxiliary._is_suspend


def test_dut_auxiliary_init_com_only(mocker):
    """Test the constructor with the connector only"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    assert auxiliary.channel == com
    assert auxiliary.flash is None


def test_create_auxiliary_instance(mocker):
    """Test create the auxiliary instance with success with the connector and the flasher"""

    com = MockCChanel()
    flash = MockFlasher()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com, flash)

    mocker.patch.object(DUTAuxiliary, "_send_ping_command", return_value=True)
    is_instantiated = auxiliary._create_auxiliary_instance()

    assert is_instantiated is True


def test_create_auxiliary_instance_fail_ping_pong(mocker):
    """Test fail to create the auxiliary instance with the connector and the flasher due to ping-pong"""

    com = MockCChanel()
    flash = MockFlasher()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com, flash)

    mocker.patch.object(DUTAuxiliary, "_send_ping_command", return_value=False)
    is_instantiated = auxiliary._create_auxiliary_instance()

    assert is_instantiated is False


def test_create_auxiliary_instance_fail_flash(mocker):
    """Test fail to create the auxiliary instance with the connector and the flasher due to flash"""

    com = MockCChanel()
    flash = MockFlasher(is_flashed=False)

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com, flash)

    mocker.patch.object(DUTAuxiliary, "_send_ping_command", return_value=True)
    is_instantiated = auxiliary._create_auxiliary_instance()

    assert is_instantiated is False


def test_create_auxiliary_instance_com_only(mocker):
    """Test create the auxiliary instance with success with the connector only"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_ping_command", return_value=True)
    is_instantiated = auxiliary._create_auxiliary_instance()

    assert is_instantiated is True


def test_create_auxiliary_instance_com_only_fail_ping_pong(mocker):
    """Test fail to create the auxiliary instance with the connector only due to ping-pong"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_ping_command", return_value=False)
    is_instantiated = auxiliary._create_auxiliary_instance()

    assert is_instantiated is False


def test_delete_auxiliary_instance(mocker):
    """Test delete the auxiliary"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    assert auxiliary._delete_auxiliary_instance() is True


def test_run_command(mocker):
    """Test run command"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_and_wait_ack", return_value=True)
    assert auxiliary._run_command(Message()) is True


def test_run_command_send_and_wait_ack_fail(mocker):
    """Test run command fail"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_and_wait_ack", return_value=False)
    assert auxiliary._run_command(Message()) is False


def test_abort_command(mocker):
    """Test abort command"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_and_wait_ack", return_value=True)
    assert auxiliary._abort_command() is True


def test_abort_command_fail(mocker):
    """Test run command fail"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(DUTAuxiliary, "_send_and_wait_ack", return_value=False)
    mocker.patch.object(DUTAuxiliary, "_delete_auxiliary_instance", return_value=None)
    mocker.patch.object(DUTAuxiliary, "_create_auxiliary_instance", return_value=None)

    assert auxiliary._abort_command() is False


def test_receive_message(mocker):
    """Test receive message"""

    receive_msg = {"msg": Message()}
    com = MockCChanel(receive_msg["msg"])

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "generate_ack_message", return_value=True)

    assert auxiliary._receive_message(1) == receive_msg["msg"]


def test_receive_message_fail(mocker):
    """Test receive message fail"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "generate_ack_message", return_value=True)

    assert auxiliary._receive_message(1) is None


def test_ping_pong(mocker):
    """Test ping-pong"""

    receive_msg = {"msg": Message(msg_type=MessageType.ACK)}
    com = MockCChanel(receive_msg)

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "check_if_ack_message_is_matching", return_value=True)

    assert auxiliary._send_ping_command(1, 1) is True


def test_ping_pong_fail(mocker):
    """Test ping-pong fail"""

    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "check_if_ack_message_is_matching", return_value=False)

    assert auxiliary._send_ping_command(1, 1) is False


def test_ping_pong_fail_wrong_message(mocker):
    """Test ping-pong fail"""

    com = MockCChanel(msg=Message())

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "check_if_ack_message_is_matching", return_value=False)

    assert auxiliary._send_ping_command(1, 1) is False


def test__send_and_wait_ack(mocker):
    """Test send and wait ack"""

    msg = Message()
    com = MockCChanel(msg=msg)

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "check_if_ack_message_is_matching", return_value=True)

    assert auxiliary._send_and_wait_ack(msg, 2, 1) is True


def test__send_and_wait_ack_fail_check(mocker):
    """Test send and wait ack fail due to check"""

    msg = Message()
    com = MockCChanel(msg=msg)

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    mocker.patch.object(Message, "check_if_ack_message_is_matching", return_value=False)

    assert auxiliary._send_and_wait_ack(msg, 2, 1) is False


def test__send_and_wait_ack_fail_receive(mocker):
    """Test send and wait ack fail due to receiving nothing"""

    msg = Message()
    com = MockCChanel()

    mocker.patch.object(AuxiliaryInterface, "start")
    auxiliary = DUTAuxiliary("connector", com)

    assert auxiliary._send_and_wait_ack(msg, 2, 1) is False


def test_resume(mocker):
    """Test if resume method call correctly handle _is_suspend flag."""
    mocker.patch.object(AuxiliaryInterface, "start")
    mock_create_inst = mocker.patch.object(AuxiliaryInterface, "create_instance")

    auxiliary = DUTAuxiliary("channel", "flasher")
    auxiliary.resume()

    assert not auxiliary._is_suspend
    mock_create_inst.assert_called_once()


def test_resume_with_error(mocker, caplog):
    """Test if resume method log an error when a issue is previously
    detected in _create_auxiliary_instance method or is_instance is not
    False."""
    mocker.patch.object(AuxiliaryInterface, "start")

    auxiliary = DUTAuxiliary("channel", "flasher")
    auxiliary.is_instance = True
    auxiliary.resume()

    assert "is already running" in caplog.text


def test_suspend(mocker):
    """Test if suspend method call correctly handle _is_suspend flag."""
    mocker.patch.object(AuxiliaryInterface, "start")
    mock_del_inst = mocker.patch.object(AuxiliaryInterface, "delete_instance")

    auxiliary = DUTAuxiliary("channel", "flasher")
    auxiliary.is_instance = True
    auxiliary.suspend()

    assert auxiliary._is_suspend
    mock_del_inst.assert_called_once()


def test_suspend_with_error(mocker, caplog):
    """Test if suspend method log an error when auxiliary instance is
    invalid (is_instance to False)"""
    mocker.patch.object(AuxiliaryInterface, "start")

    auxiliary = DUTAuxiliary("channel", "flasher")
    auxiliary.suspend()

    assert "is already stopped" in caplog.text


@pytest.mark.parametrize(
    "logger_names, loggers_to_activate, expected_level",
    [
        (["pylink", "pylink.jlink"], ["pylink", "pylink.jlink"], logging.DEBUG),
        (["pylink", "pylink.jlink"], None, logging.WARNING),
        (["pylink", "pylink.jlink"], ["pylink"], logging.DEBUG),
        (["pylink", "pylink.jlink"], ["pylink.jlink"], logging.DEBUG),
        (["pylink", "pylink.jlink"], ["all"], logging.DEBUG),
    ],
)
def test_initialize_loggers(mocker, logger_names, loggers_to_activate, expected_level):
    """Test the logger activation from AuxiliaryInterface"""

    mocker.patch.object(AuxiliaryInterface, "start")
    mocker.patch.object(CCRttSegger, "_cc_open")
    connector = CCRttSegger()

    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

    auxiliary = DUTAuxiliary(com=connector, activate_log=loggers_to_activate)

    for logger_name in logger_names:
        assert logging.getLogger(logger_name).level == expected_level


def test_initialize_loggers_default(mocker):
    """Test the default logger activation from AuxiliaryInterface"""

    aux_log = logging.getLogger("my_auxiliary")
    pykiso_log = logging.getLogger("pykiso.test_suite.dynamic_loader")

    mocker.patch.object(AuxiliaryInterface, "start")

    aux_log.setLevel(logging.DEBUG)
    pykiso_log.setLevel(logging.DEBUG)

    auxiliary = DUTAuxiliary(activate_log=None)

    assert aux_log.level == logging.DEBUG
    assert pykiso_log.level == logging.DEBUG
