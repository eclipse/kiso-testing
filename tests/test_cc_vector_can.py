##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import importlib
import logging
import sys

import can as python_can
import pytest

from pykiso import Message
from pykiso.lib.connectors import cc_vector_can
from pykiso.lib.connectors.cc_vector_can import CCVectorCan, can, detect_serial_number
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

    mocker.patch.object(can.interface, "Bus", new=MockCan)
    return can.interface


def test_import():
    with pytest.raises(ImportError):
        sys.modules["can"] = None
        importlib.reload(cc_vector_can)
    sys.modules["can"] = can
    importlib.reload(cc_vector_can)


@pytest.mark.parametrize(
    "constructor_params, expected_config",
    [
        (
            {},
            {
                "bustype": "vector",
                "poll_interval": 0.01,
                "rx_queue_size": 524288,
                "serial": None,
                "channel": 3,
                "bitrate": 500000,
                "data_bitrate": 2000000,
                "fd": True,
                "enable_brs": False,
                "app_name": None,
                "can_filters": None,
                "is_extended_id": False,
            },
        ),
        (
            {
                "bustype": "vector",
                "poll_interval": 0.01,
                "rx_queue_size": 524288,
                "serial": None,
                "channel": 3,
                "bitrate": 500000,
                "data_bitrate": 2000000,
                "fd": False,
                "enable_brs": True,
                "app_name": None,
                "can_filters": None,
                "is_extended_id": False,
            },
            {
                "bustype": "vector",
                "poll_interval": 0.01,
                "rx_queue_size": 524288,
                "serial": None,
                "channel": 3,
                "bitrate": 500000,
                "data_bitrate": 2000000,
                "fd": False,
                "enable_brs": True,
                "app_name": None,
                "can_filters": None,
                "is_extended_id": False,
            },
        ),
    ],
)
def test_constructor(constructor_params, expected_config, caplog):
    param = constructor_params.values()

    with caplog.at_level(logging.INTERNAL_WARNING):
        can_inst = CCVectorCan(*param)

    assert can_inst.bustype == expected_config["bustype"]
    assert can_inst.channel == expected_config["channel"]
    assert can_inst.rx_queue_size == expected_config["rx_queue_size"]
    assert can_inst.poll_interval == expected_config["poll_interval"]
    assert can_inst.data_bitrate == expected_config["data_bitrate"]
    assert can_inst.bitrate == expected_config["bitrate"]
    assert can_inst.app_name == expected_config["app_name"]
    assert can_inst.serial == expected_config["serial"]
    assert can_inst.fd == expected_config["fd"]
    assert can_inst.bus == None
    assert can_inst.remote_id == None
    assert can_inst.is_extended_id == expected_config["is_extended_id"]
    assert can_inst.can_filters == expected_config["can_filters"]
    assert can_inst.timeout == 1e-6

    if not can_inst.fd and can_inst.enable_brs:
        assert "Bitrate switch will have no effect" in caplog.text


def test_cc_open(mock_can_bus):
    can_inst = CCVectorCan()
    can_inst._cc_open()

    assert isinstance(can_inst.bus, mock_can_bus.Bus) == True
    assert can_inst.bus != None


def test_cc_close(mock_can_bus):

    with CCVectorCan() as can_inst:
        pass

    mock_can_bus.Bus.shutdown.assert_called_once()
    assert can_inst.bus == None


@pytest.mark.parametrize(
    "parameters ,raw",
    [
        ({"msg": b"\x10\x36", "remote_id": 0x0A}, True),
        ({"msg": b"\x10\x36", "remote_id": None}, True),
        ({"msg": b"\x10\x36", "remote_id": 10}, True),
        ({"msg": b"", "remote_id": 10}, True),
        ({"msg": message_with_tlv, "remote_id": 0x0A}, False),
        ({"msg": message_with_no_tlv, "remote_id": 0x0A}, False),
        ({"msg": message_with_no_tlv}, False),
        ({"msg": message_with_no_tlv, "remote_id": 36}, False),
    ],
)
def test_cc_send(mock_can_bus, parameters, raw):
    if not raw:
        parameters["msg"] = parameters.get("msg").serialize()
    with CCVectorCan() as can:
        can.remote_id = 0x500
        can._cc_send(**parameters)

    mock_can_bus.Bus.send.assert_called_once()
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    "raw_data, can_id, timeout, raw ,expected_type ,timestamp",
    [
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", 0x500, 10, False, Message, 1),
        (
            b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
            0x207,
            None,
            None,
            Message,
            2,
        ),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 10, True, bytearray, 3),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 0, True, bytearray, 4),
    ],
)
def test_can_recv(
    mocker, mock_can_bus, raw_data, can_id, timeout, raw, expected_type, timestamp
):
    mocker.patch(
        "can.interface.Bus.recv",
        return_value=python_can.Message(
            data=raw_data, arbitration_id=can_id, timestamp=timestamp
        ),
    )
    with CCVectorCan() as can:
        response = can._cc_receive(timeout)

    msg_received = response.get("msg")
    id_received = response.get("remote_id")
    if not raw:
        msg_received = Message.parse_packet(msg_received)

    assert response.get("timestamp") == timestamp
    assert isinstance(msg_received, expected_type) == True
    assert id_received == can_id
    mock_can_bus.Bus.recv.assert_called_once_with(timeout=timeout or 1e-6)
    mock_can_bus.Bus.shutdown.assert_called_once()


@pytest.mark.parametrize(
    " side_effect_value, expected_log",
    [
        (None, ""),
        (BaseException, "encountered error while receiving message via"),
    ],
)
def test_can_recv_invalid(
    mocker, mock_can_bus, side_effect_value, caplog, expected_log
):

    mocker.patch(
        "can.interface.Bus.recv", return_value=None, side_effect=side_effect_value
    )

    with caplog.at_level(logging.ERROR):
        with CCVectorCan() as can:
            response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    "serial_number_list, serial_number_list_empty",
    [
        (
            [1111, 2222],
            [0],
        ),
    ],
)
def test_detect_serial_number(mocker, serial_number_list, serial_number_list_empty):
    class MockXLchannelConfig:
        """Class used to stub vector.vxlapi.XLchannelConfig() class"""

        def __init__(
            self,
            serial: int = 0,
            **kwargs,
        ):
            """
            :param serial: serial number of the channel configuration
            """
            self.serial_number = serial

    # 1) Detection of the lowest serial number in the channels list:
    mocker.patch(
        "pykiso.lib.connectors.cc_vector_can.get_channel_configs",
        return_value=[
            MockXLchannelConfig(serial=serial) for serial in serial_number_list
        ],
    )
    can_inst = CCVectorCan(serial="AUTO")
    assert min(serial_number_list) == can_inst.serial

    # 2) Raise an error if no Vector Box:
    mocker.patch(
        "pykiso.lib.connectors.cc_vector_can.get_channel_configs",
        return_value=[
            MockXLchannelConfig(serial=serial) for serial in serial_number_list_empty
        ],
    )
    with pytest.raises(ConnectionRefusedError) as e:
        detect_serial_number()
    assert str(e.value) == "No Vector box is currently available"
