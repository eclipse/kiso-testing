##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import pytest

from pykiso.lib.auxiliaries.ykush_auxiliary import (
    YKUSH_PORT_STATE_OFF,
    YKUSH_PORT_STATE_ON,
    YkushAuxiliary,
    YkushDeviceNotFound,
    YkushPortNumberError,
    YkushSetStateError,
    YkushStatePortNotRetrieved,
)


@pytest.fixture
def hid_device_mock(mocker):
    return mocker.patch("hid.device")


@pytest.fixture
def hid_enumerate_mock(mocker):

    return mocker.patch("hid.enumerate")


@pytest.fixture
def ykush_aux_instance(hid_device_mock):
    return YkushAuxiliaryMocker(hid_device_mock)


@pytest.fixture
def raw_send_receive_mock(ykush_aux_instance, mocker):
    return mocker.patch.object(ykush_aux_instance, "_raw_sendreceive")


@pytest.fixture
def get_port_mock(ykush_aux_instance, mocker):
    return mocker.patch.object(ykush_aux_instance, "get_port_state")


@pytest.fixture
def get_all_port_mock(ykush_aux_instance, mocker):
    return mocker.patch.object(ykush_aux_instance, "get_all_ports_state")


class YkushAuxiliaryMocker(YkushAuxiliary):
    """Class used to test the function that are mocked in the init"""

    def __init__(self, hid_device_mock):
        self._ykush_device = hid_device_mock
        self._product_id = "test_product_id"
        self._path = "test_path"
        self.number_of_port = 3


@pytest.fixture
def raw_send_mock(mocker, ykush_aux_instance):
    return mocker.patch.object(ykush_aux_instance, "_raw_sendreceive")


def test_no_ykush_device_found_init():
    with pytest.raises(YkushDeviceNotFound):
        YkushAuxiliary(serial_number=12)


def test_ykush_instance(mocker, ykush_aux_instance):
    power_on_mocker = mocker.patch.object(ykush_aux_instance, "set_all_ports_on")
    is_instantiated = ykush_aux_instance._create_auxiliary_instance()
    assert is_instantiated
    power_on_mocker.assert_called_once()

    result = ykush_aux_instance._delete_auxiliary_instance()
    assert result
    assert power_on_mocker.call_count == 2


def test_find_device_path(hid_device_mock, ykush_aux_instance):
    path = "test"

    ykush_aux_instance.find_device(path=path)

    hid_device_mock.assert_called_once()


def test_find_device_serial(ykush_aux_instance, hid_enumerate_mock):
    serial = "YK28389"
    device = {
        "vendor_id": 0x04D8,
        "product_id": 0x0042,
        "serial_number": serial,
        "path": "test_path",
    }
    hid_enumerate_mock.return_value = [device]

    ykush_aux_instance.find_device(serial=serial)

    hid_enumerate_mock.assert_called_once_with(0, 0)
    assert ykush_aux_instance._product_id == device["product_id"]
    assert ykush_aux_instance._path == device["path"]


@pytest.mark.parametrize(
    "list_device_returned",
    [
        ([]),
        (
            [
                {
                    "vendor_id": 0x04D8,
                    "product_id": 0x0042,
                    "serial_number": "YK28389",
                    "path": "test_path",
                }
            ]
        ),
    ],
)
def test_find_device_no_device_found(
    ykush_aux_instance, hid_enumerate_mock, list_device_returned
):
    hid_enumerate_mock.return_value = list_device_returned
    ykush_aux_instance._ykush_device = None
    with pytest.raises(YkushDeviceNotFound):
        ykush_aux_instance.find_device(serial=12)

    hid_enumerate_mock.assert_called_once_with(0, 0)


def test_check_port_number(ykush_aux_instance):
    port_number = 12
    with pytest.raises(YkushPortNumberError):
        ykush_aux_instance.check_port_number(port_number)


@pytest.mark.parametrize("state,str_expected", [(1, "ON"), (0, "OFF"), (255, "ERROR")])
def test_get_str_state(ykush_aux_instance, state, str_expected):
    state_str = ykush_aux_instance.get_str_state(state)
    assert state_str == str_expected


@pytest.mark.parametrize(
    "product_id,number_port_expected",
    [(0xF0CD, 1), (0x0042, 3)],
)
def test_get_number_of_port(
    ykush_aux_instance,
    product_id,
    number_port_expected,
):
    ykush_aux_instance._product_id = product_id

    number_port = ykush_aux_instance.get_number_of_port()

    assert number_port == number_port_expected


@pytest.mark.parametrize(
    "state,state_returned,port_number,msg_to_send",
    [
        (YKUSH_PORT_STATE_ON, YKUSH_PORT_STATE_ON, 1, [0x11]),
        (YKUSH_PORT_STATE_ON, YKUSH_PORT_STATE_ON, 2, [0x12]),
        (YKUSH_PORT_STATE_ON, YKUSH_PORT_STATE_ON, 3, [0x13]),
        (YKUSH_PORT_STATE_OFF, YKUSH_PORT_STATE_OFF, 1, [0x01]),
        (YKUSH_PORT_STATE_OFF, YKUSH_PORT_STATE_OFF, 2, [0x02]),
        (YKUSH_PORT_STATE_OFF, YKUSH_PORT_STATE_OFF, 3, [0x03]),
    ],
    ids=[
        "port 1 on",
        "port 2 on",
        "port 3 on",
        "port 1 off",
        "port 2 off",
        "port 3 off",
    ],
)
def test_set_port_state(
    ykush_aux_instance,
    state,
    state_returned,
    port_number,
    msg_to_send,
    get_port_mock,
    mocker,
):
    get_port_mock.return_value = state_returned

    raw_send_mock = mocker.patch.object(ykush_aux_instance, "_raw_sendreceive")

    ykush_aux_instance.set_port_state(port_number, state)

    get_port_mock.assert_called_once_with(port_number)
    raw_send_mock.assert_called_once_with(msg_to_send)


@pytest.mark.parametrize(
    "state,state_returned",
    [
        (YKUSH_PORT_STATE_ON, YKUSH_PORT_STATE_OFF),
        (YKUSH_PORT_STATE_OFF, YKUSH_PORT_STATE_ON),
    ],
    ids=["port on fail", "port off fail"],
)
def test_set_port_state_fail(
    ykush_aux_instance, state, state_returned, raw_send_mock, get_port_mock
):
    port_number = 1
    get_port_mock.return_value = state_returned

    with pytest.raises(YkushSetStateError):
        ykush_aux_instance.set_port_state(port_number, state)
    get_port_mock.assert_called_once_with(port_number)
    raw_send_mock.assert_called_once()


def test_set_port_state_fail_state_not_found(
    ykush_aux_instance, raw_send_mock, get_port_mock
):
    port_number = 1
    get_port_mock.side_effect = YkushStatePortNotRetrieved()

    with pytest.raises(YkushSetStateError):
        ykush_aux_instance.set_port_state(port_number, YKUSH_PORT_STATE_ON)
    get_port_mock.assert_called_once_with(port_number)
    raw_send_mock.assert_called_once()


def test_set_port_on(ykush_aux_instance, mocker):
    port_number = 1
    set_port_state_mock = mocker.patch.object(ykush_aux_instance, "set_port_state")

    ykush_aux_instance.set_port_on(port_number)

    set_port_state_mock.assert_called_once_with(port_number, state=YKUSH_PORT_STATE_ON)


def test_set_port_off(ykush_aux_instance, mocker):
    port_number = 1
    set_port_state_mock = mocker.patch.object(ykush_aux_instance, "set_port_state")

    ykush_aux_instance.set_port_off(port_number)

    set_port_state_mock.assert_called_once_with(port_number, state=YKUSH_PORT_STATE_OFF)


@pytest.mark.parametrize(
    "state_wanted,states_returned,message_expected",
    [
        (YKUSH_PORT_STATE_ON, [YKUSH_PORT_STATE_ON] * 3, [0x1A]),
        (YKUSH_PORT_STATE_OFF, [YKUSH_PORT_STATE_OFF] * 3, [0x0A]),
    ],
    ids=["all ports on success", "all ports off success"],
)
def test_set_all_ports(
    ykush_aux_instance,
    state_wanted,
    states_returned,
    message_expected,
    raw_send_mock,
    get_all_port_mock,
):
    get_all_port_mock.return_value = states_returned

    ykush_aux_instance.set_all_ports(state=state_wanted)

    get_all_port_mock.assert_called_once()
    raw_send_mock.assert_called_once_with(message_expected)


@pytest.mark.parametrize(
    "state,state_returned",
    [
        (YKUSH_PORT_STATE_ON, [YKUSH_PORT_STATE_OFF, YKUSH_PORT_STATE_ON]),
        (YKUSH_PORT_STATE_OFF, [YKUSH_PORT_STATE_ON, YKUSH_PORT_STATE_OFF]),
    ],
    ids=["port on fail", "port off fail"],
)
def test_set_all_ports_state_fail(
    ykush_aux_instance, state, state_returned, raw_send_mock, get_all_port_mock
):
    get_all_port_mock.return_value = state_returned

    with pytest.raises(YkushSetStateError):
        ykush_aux_instance.set_all_ports(state)
    get_all_port_mock.assert_called_once_with()
    raw_send_mock.assert_called_once()


def test_set_all_ports_state_fail_state_not_found(
    ykush_aux_instance, raw_send_mock, get_all_port_mock
):
    get_all_port_mock.side_effect = YkushStatePortNotRetrieved()

    with pytest.raises(YkushSetStateError):
        ykush_aux_instance.set_all_ports(YKUSH_PORT_STATE_ON)
    get_all_port_mock.assert_called_once_with()
    raw_send_mock.assert_called_once()


@pytest.mark.parametrize(
    "state_wanted,states_returned,message_expected",
    [
        (YKUSH_PORT_STATE_ON, [YKUSH_PORT_STATE_ON] * 3, [0x1A]),
        (YKUSH_PORT_STATE_OFF, [YKUSH_PORT_STATE_OFF] * 3, [0x0A]),
    ],
    ids=["all ports on success", "all ports off success"],
)
def test_set_all_ports_fails(
    ykush_aux_instance,
    state_wanted,
    states_returned,
    message_expected,
    raw_send_mock,
    get_all_port_mock,
):
    get_all_port_mock.return_value = states_returned

    ykush_aux_instance.set_all_ports(state=state_wanted)

    get_all_port_mock.assert_called_once()
    raw_send_mock.assert_called_once_with(message_expected)


def test_set_allports_on(ykush_aux_instance, mocker):
    set_port_state_mock = mocker.patch.object(ykush_aux_instance, "set_all_ports")

    ykush_aux_instance.set_all_ports_on()

    set_port_state_mock.assert_called_once_with(state=YKUSH_PORT_STATE_ON)


def test_set_allports_off(ykush_aux_instance, mocker):
    set_port_state_mock = mocker.patch.object(ykush_aux_instance, "set_all_ports")

    ykush_aux_instance.set_all_ports_off()

    set_port_state_mock.assert_called_once_with(state=YKUSH_PORT_STATE_OFF)


@pytest.mark.parametrize(
    "state_returned,state_expected,port_number",
    [([1, 0, 0], 1, 1), ([0, 1, 0], 1, 2), ([1, 1, 0], 0, 3)],
)
def test_get_port_state(
    ykush_aux_instance, state_returned, state_expected, port_number, get_all_port_mock
):
    get_all_port_mock.return_value = state_returned

    state = ykush_aux_instance.get_port_state(port_number)

    assert state == state_expected
    get_all_port_mock.assert_called_once()


@pytest.mark.parametrize(
    "state_returned,state_expected",
    [([0x1, 0x1, 0x2, 0x17], [0, 0, 1]), ([0x1, 0x18, 0x19, 0x17], [1, 1, 1])],
)
def test_get_all_ports_state(
    ykush_aux_instance, raw_send_receive_mock, state_returned, state_expected
):
    raw_send_receive_mock.return_value = state_returned

    state_ports = ykush_aux_instance.get_all_ports_state()

    assert state_expected == state_ports
    raw_send_receive_mock.assert_called_with([0x2A])


def test_get_all_ports_state_fail(ykush_aux_instance, raw_send_receive_mock):
    raw_send_receive_mock.return_value = [0x0, 0x1, 0x1, 0x1]

    with pytest.raises(YkushStatePortNotRetrieved):
        ykush_aux_instance.get_all_ports_state()


def test_get_all_ports_state_firmware_version_inferior_1(
    ykush_aux_instance, mocker, raw_send_receive_mock
):
    get_firmware_version_mock = mocker.patch.object(
        ykush_aux_instance, "get_firmware_version", return_value=[0.2]
    )
    raw_send_receive_mock.side_effect = [[0x1, 0x1], [0x1, 0x17], [0x1, 0x3]]

    list_states = ykush_aux_instance.get_all_ports_state()

    assert list_states == [0, 1, 0]
    get_firmware_version_mock.assert_called_once()


def test_get_all_ports_state_firmware_version_inferior_1_fail(
    ykush_aux_instance, mocker, raw_send_receive_mock
):
    get_firmware_version_mock = mocker.patch.object(
        ykush_aux_instance, "get_firmware_version", return_value=[0.2]
    )
    raw_send_receive_mock.side_effect = [[0x0, 0x1], [0x1, 0x17], [0x1, 0x3]]
    with pytest.raises(YkushStatePortNotRetrieved):
        list_states = ykush_aux_instance.get_all_ports_state()

    get_firmware_version_mock.assert_called_once()


@pytest.mark.parametrize("state_port,bool_expected", [(1, True), (0, False)])
def test_is_port_on(ykush_aux_instance, mocker, state_port, bool_expected):
    get_port_state_mock = mocker.patch.object(
        ykush_aux_instance, "get_port_state", return_value=state_port
    )
    port_number = 1

    state = ykush_aux_instance.is_port_on(port_number)

    assert state == bool_expected
    get_port_state_mock.assert_called_once_with(port_number)


@pytest.mark.parametrize("state_port,bool_expected", [(1, False), (0, True)])
def test_is_port_off(ykush_aux_instance, mocker, state_port, bool_expected):
    get_port_state_mock = mocker.patch.object(
        ykush_aux_instance, "get_port_state", return_value=state_port
    )
    port_number = 1

    state = ykush_aux_instance.is_port_off(port_number)

    assert state == bool_expected
    get_port_state_mock.assert_called_once_with(port_number)


@pytest.mark.parametrize(
    "packet_received,msg_expected",
    [([0x0] * 65, [0x0] * 20), (None, [0xFF] * 20), ([0x0], [0xFF] * 20)],
)
def test__raw_sendreceive(
    ykush_aux_instance, mocker, hid_device_mock, packet_received, msg_expected
):
    mocker.patch.object(ykush_aux_instance, "_open_and_close_device")
    hid_device_mock.read.return_value = packet_received

    msg = ykush_aux_instance._raw_sendreceive(packetarray=[0x1])

    assert msg == msg_expected
    hid_device_mock.read.assert_called_once()
