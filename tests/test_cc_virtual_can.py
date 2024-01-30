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

        shutdown = mocker.stub(name="shutdown")
        send = mocker.stub(name="send")
        recv = mocker.stub(name="recv")

    mocker.patch.object(can.interface, "Bus", new=MockUdp)
    return can.interface


def test_constructor(mock_vcan_bus):

    vcan_inst = CCVirtualCan(
        channel=UdpMulticastBus.DEFAULT_GROUP_IPv4,
        interface="udp_multicast", 
        receive_own_messages=False,
        is_fd = False,
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

        assert vcan_inst.bus == None
        assert not caplog.records


def test_cc_open(
    mock_vcan_bus, caplog
):
    logging.getLogger("pykiso.lib.connectors.cc_virtual_can.log")

    vcan_inst = CCVirtualCan()
    assert vcan_inst.is_open is False
    vcan_inst._cc_open()

    assert vcan_inst.bus != None
    assert vcan_inst.is_open is True

    vcan_inst._cc_open()

    assert vcan_inst.bus != None
    assert vcan_inst.is_open is True
    assert "is already open" in caplog.text


def test_cc_send(mock_vcan_bus):

    with CCVirtualCan() as vcan:
        vcan.bus = mock_vcan_bus.Bus
        vcan._cc_send(b"\x10\x36", 0x0A)

    mock_vcan_bus.Bus.send.assert_called_once()
    mock_vcan_bus.Bus.shutdown.assert_called_once()
    

def test_can_recv(mock_vcan_bus):
    mock_vcan_bus.Bus.recv.return_value = python_can.Message(
        data=b"\x40\x01\x03\x00\x02\x03\x00", arbitration_id=0x502, timestamp=10
    )

    with CCVirtualCan() as vcan:
        vcan.bus = mock_vcan_bus.Bus
        response = vcan._cc_receive(3)


    assert response.get("timestamp") == 10
    assert response.get("remote_id") == 0x502
    mock_vcan_bus.Bus.recv.assert_called_once_with(timeout=3 or 1e-6)

    
def test_can_recv_invalid(mocker, mock_vcan_bus):

    mocker.patch("can.interface.Bus.recv", return_value={"msg": None})

    with CCVirtualCan() as vcan:
        response = vcan._cc_receive(timeout=0.0001)

    assert response["msg"] is None
    assert response.get("remote_id") is None


def test_can_recv_exception(caplog, mock_vcan_bus, mocker):

    mocker.patch("can.interface.Bus.recv", side_effect=Exception())
    logging.getLogger("pykiso.lib.connectors.cc_virtual_can.log")
    with CCVirtualCan() as can:
        can.bus = mock_vcan_bus.Bus
        response = can._cc_receive(timeout=0.0001)

        assert response["msg"] is None
        assert response.get("remote_id") is None
        assert "Exception" in caplog.text

def test_can_recv_error(caplog, mock_vcan_bus, mocker):

    mocker.patch("can.interface.Bus.recv", side_effect=python_can.CanError())
    logging.getLogger("pykiso.lib.connectors.cc_virtual_can.log")
    with CCVirtualCan() as can:
        can.bus = mock_vcan_bus.Bus
        response = can._cc_receive(timeout=0.0001)

        assert response["msg"] is None
        assert response.get("remote_id") is None
        assert "encountered CAN error while receiving message" in caplog.text