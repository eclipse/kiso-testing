import pytest
import logging
from unittest import mock
from pykiso import Message

import can as python_can
from pykiso.lib.connectors.cc_virtual_can import CCVirtualCan
from can.interfaces.udp_multicast.bus import UdpMulticastBus
from pykiso.lib.connectors.cc_pcan_can.cc_pcan_can import can

@pytest.fixture
def mock_vcan_bus(mocker):
    """fixture used to create mocker relative to can object from
    python-can package.
    """

    class MockUdp:
        """Class used to stub can.interface.Bus method"""

        def __init__(self, **kwargs):
            """"""
            pass
        
        msg = can.Message(
            501,
            b'\x01\x02\x03\x04\x05',
            True,
            len(b'\x01\x02\x03\x04\x05'),
            False,
            False,
            True,
        )

        shutdown = mocker.stub(name="shutdown")
        send = mocker.stub(name="send")
        recv = mocker.stub(name="recv")

    mocker.patch.object(can.interface, "Bus", new=MockUdp)
    return can.interface


@pytest.mark.parametrize(
    "constructor_params, expected_config",

)
def test_constructor(constructor_params, expected_config, caplog, mocker):

    vcan_inst = CCVirtualCan(
        channel=UdpMulticastBus.DEFAULT_GROUP_IPv4,
        interface="udp_multicast", 
        receive_own_messages=False,
        fd = False,
    )
    
    assert vcan_inst.interface == "udp_multicast"
    assert vcan_inst.channel == UdpMulticastBus.DEFAULT_GROUP_IPv4
    assert vcan_inst.receive_own_messages == False
    assert vcan_inst.is_fd == False
    assert vcan_inst.enable_brs == False
    assert vcan_inst.is_extended_id == False
    assert vcan_inst._is_open == False
    assert vcan_inst.config == {
        "interface": "udp_multicast",
        "channel":  UdpMulticastBus.DEFAULT_GROUP_IPv4,
        "preserve_timestamps": False,
        "receive_own_messages":False,
        "fd": False,
    }

def test_cc_close(
    caplog,
    mock_vcan_bus,
):

    with caplog.at_level(logging.ERROR, logger="pykiso.lib.connectors.cc_pcan_can.log"):
        with CCVirtualCan() as vcan_inst:
            pass

        mock_vcan_bus.Bus.shutdown.assert_called_once()
        assert vcan_inst.bus == None
        assert not caplog.records


def test_cc_open(
    mock_vcan_bus,
):
    vcan_inst = CCVirtualCan()
    assert vcan_inst.is_open is False
    vcan_inst._cc_open()

    assert isinstance(vcan_inst.bus, mock_vcan_bus.Bus) == True
    assert vcan_inst.bus != None
    assert vcan_inst.is_open is True


def test_cc_send(mock_vcan_bus):
    vcan_inst = CCVirtualCan()
    msg = b'\x01\x02\x03\x04\x05'
    vcan_inst._cc_send(msg, 501)
    mock_vcan_bus.Bus.send.called_with(
        501,
        msg,
        True,
        len(msg),
        False,
        False,
        True,
    )

@pytest.mark.parametrize(
    "raw_data, can_id, timeout, raw,expected_type, timestamp",
    [
        (b"\x40\x01\x03\x00\x01\x02\x03\x00", 0x500, 10, Message, 1),
        (
            b"\x40\x01\x03\x00\x01\x02\x03\x09\x6e\x02\x4f\x4b\x70\x03\x12\x34\x56",
            0x207,
            None,
            Message,
            2,
        ),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 10, bytearray, 3),
        (b"\x40\x01\x03\x00\x02\x03\x00", 0x502, 0, bytearray, 4),
    ],
)
def test_can_recv(
    mock_can_bus,
    raw_data,
    can_id,
    timeout,
    timestamp,
    expected_type,
    mock_vcan_bus,
):
    mock_vcan_bus.Bus.recv.return_value = python_can.Message(
        data=raw_data, arbitration_id=can_id, timestamp=timestamp
    )

    with CCVirtualCan() as can:
        response = can._cc_receive(timeout)

    msg_received = response.get("msg")

    assert response.get("timestamp") == timestamp
    assert isinstance(msg_received, expected_type)
    assert response.get("remote_id") == can_id
    mock_can_bus.Bus.recv.assert_called_once_with(timeout=timeout or 1e-6)

    
def test_can_recv_invalid(mocker, mock_vcan_bus):

    mocker.patch("can.interface.Bus.recv", return_value={"msg": None})

    with CCVirtualCan() as can:
        response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None


def test_can_recv_exception(caplog, mocker, mock_vcan_bus):

    mocker.patch("can.interface.Bus.recv", side_effect=Exception())
    logging.getLogger("pykiso.lib.connectors.cc_virtual_can.log")

    with CCVirtualCan() as can:
        response = can._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None
    assert "Exception" in caplog.text