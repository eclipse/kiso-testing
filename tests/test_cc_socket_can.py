##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
from unittest import mock

import can as python_can
import pytest

from pykiso import Message
from pykiso.lib.connectors.cc_socket_can.cc_socket_can import CCSocketCan, can
from pykiso.message import MessageCommandType, MessageType, TlvKnownTags

tlv_dict_to_send = {
    TlvKnownTags.TEST_REPORT: "OK",
    TlvKnownTags.FAILURE_REASON: b"\x12\x34\x56",
}

message_with_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
    tlv_dict=tlv_dict_to_send,
)

message_with_no_tlv = Message(
    msg_type=MessageType.COMMAND,
    sub_type=MessageCommandType.TEST_CASE_SETUP,
    test_suite=2,
    test_case=3,
)


@pytest.fixture
def mock_can_bus(mocker):
    """fixture used to create mocker relative to can object from
    python-can package.
    """

    class MockCan:
        """Class used to stub can.interface.Bus method"""

        def __init__(self, **kwargs):
            """"""
            pass

        set_filters = mocker.stub(name="set_filters")
        shutdown = mocker.stub(name="shutdown")
        send = mocker.stub(name="send")
        recv = mocker.stub(name="recv")

    mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.cc_socket_can.os_name",
        return_value="Linux",
    )
    mocker.patch.object(can.interface, "Bus", new=MockCan)
    return can.interface


@pytest.mark.parametrize(
    "constructor_params, expected_config",
    [
        (
            {},
            {
                "channel": "vcan0",
                "remote_id": None,
                "is_fd": True,
                "enable_brs": False,
                "can_filters": [],
                "is_extended_id": True,
                "receive_own_messages": False,
                "logging_activated": False,
            },
        ),
        (
            {
                "channel": "vcan0",
                "remote_id": 0x666,
                "is_fd": False,
                "enable_brs": True,
                "can_filters": [
                    {"can_id": 0x507, "can_mask": 0x7FF, "extended": False}
                ],
                "is_extended_id": False,
                "receive_own_messages": True,
                "logging_activated": True,
            },
            {
                "channel": "vcan0",
                "remote_id": 0x666,
                "is_fd": False,
                "enable_brs": True,
                "can_filters": [
                    {"can_id": 0x507, "can_mask": 0x7FF, "extended": False}
                ],
                "is_extended_id": False,
                "receive_own_messages": True,
                "logging_activated": True,
            },
        ),
    ],
)
def test_constructor(constructor_params, expected_config, caplog):
    param = constructor_params.values()

    with caplog.at_level(logging.WARNING):
        can_inst = CCSocketCan(*param)

    assert can_inst.channel == expected_config["channel"]
    assert can_inst.remote_id == expected_config["remote_id"]
    assert can_inst.is_fd == expected_config["is_fd"]
    assert can_inst.enable_brs == expected_config["enable_brs"]
    assert can_inst.can_filters == expected_config["can_filters"]
    assert can_inst.receive_own_messages == expected_config["receive_own_messages"]
    assert can_inst.logging_activated == expected_config["logging_activated"]

    if not can_inst.is_fd and can_inst.enable_brs:
        assert "Bitrate switch will have no effect" in caplog.text


@pytest.mark.parametrize(
    "logging_requested",
    [
        (True),
        (False),
    ],
)
def test_cc_open(logging_requested, mock_can_bus, mocker):

    mock_logger = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.cc_socket_can.SocketCan2Trc"
    )

    can_inst = CCSocketCan(logging_activated=logging_requested)
    can_inst._cc_open()

    assert isinstance(can_inst.bus, mock_can_bus.Bus) == True
    assert can_inst.bus != None

    if logging_requested:
        assert isinstance(can_inst.logger, mocker.MagicMock)
        assert mock_logger.mock_calls[1] == mock.call().start()
        mock_logger.assert_called_once()


def test_cc_open_wrong_os(mocker):

    mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.cc_socket_can.os_name",
        return_value="Windows",
    )
    mock_logger = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.cc_socket_can.SocketCan2Trc"
    )

    can_inst = CCSocketCan()
    with pytest.raises(OSError, match=r"socketCAN is only available under linux"):
        can_inst._cc_open()


@pytest.mark.parametrize(
    "logging_requested",
    [
        (True),
        (False),
    ],
)
def test_cc_close(logging_requested, mock_can_bus, mocker):

    mock_logger = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.cc_socket_can.SocketCan2Trc"
    )

    can_inst = CCSocketCan(logging_activated=True)
    can_inst._cc_open()

    can_inst._cc_close()

    mock_can_bus.Bus.shutdown.assert_called_once()
    assert can_inst.bus == None

    assert can_inst.logger == None


@pytest.mark.parametrize(
    "parameters",
    [
        (b"\x10\x36", 0x0A, True),
        (b"\x10\x36", None, True),
        (b"\x10\x36", 10, True),
        (b"", 10, True),
        (message_with_tlv, 0x0A, False),
        (message_with_no_tlv, 0x0A, False),
        (message_with_no_tlv,),
        (message_with_no_tlv, 36),
    ],
)
def test_cc_send(mock_can_bus, parameters):

    with CCSocketCan(remote_id=0x0A) as can:
        can._cc_send(*parameters)

    mock_can_bus.Bus.send.assert_called_once()
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_data, can_id, cc_receive_param,expected_type",
    [
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", 0x500, (10, False), Message),
        (
            b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
            0x207,
            (None, None),
            Message,
        ),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, (10, True), bytearray),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, (0, True), bytearray),
    ],
)
def test_can_recv(
    mocker, mock_can_bus, raw_data, can_id, cc_receive_param, expected_type
):
    mock_bus_recv = mocker.patch(
        "can.interface.Bus.recv",
        return_value=python_can.Message(data=raw_data, arbitration_id=can_id),
    )
    with CCSocketCan() as can:
        msg_received, id_received = can._cc_receive(*cc_receive_param)

    assert isinstance(msg_received, expected_type) == True
    assert id_received == can_id
    mock_can_bus.Bus.recv.assert_called_once_with(timeout=cc_receive_param[0] or 1e-6)
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_state",
    [
        True,
        False,
    ],
)
def test_can_recv_invalid(mocker, mock_can_bus, raw_state):

    mocker.patch("can.interface.Bus.recv", return_value=None)

    with CCSocketCan() as can:
        msg_received, id_received = can._cc_receive(timeout=0.0001, raw=raw_state)

    assert msg_received == None
    assert id_received == None


def test_can_recv_exception(caplog, mocker, mock_can_bus):

    mocker.patch("can.interface.Bus.recv", side_effect=Exception())

    logging.getLogger("pykiso.lib.connectors.cc_socket_can.cc_socket_can.log")

    with CCSocketCan() as can:
        msg_received, id_received = can._cc_receive(timeout=0.0001)

    assert msg_received == None
    assert id_received == None
    assert "Exception" in caplog.text


def test_can_recv_can_error_exception(caplog, mocker, mock_can_bus):

    mocker.patch(
        "can.interface.Bus.recv", side_effect=python_can.CanError("Invalid Message")
    )

    logging.getLogger("pykiso.lib.connectors.cc_pcan_can.log")

    with caplog.at_level(logging.DEBUG):

        with CCSocketCan() as can:
            msg_received, id_received = can._cc_receive(timeout=0.0001)

    assert msg_received == None
    assert id_received == None
    assert "encountered can error: Invalid Message" in caplog.text
