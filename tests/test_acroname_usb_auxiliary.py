##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging

import brainstem
import pytest
from brainstem.result import Result

from pykiso.lib.auxiliaries.acroname_auxiliary import AcronameAuxiliary


@pytest.fixture
def mock_brainstem_usb(mocker):
    """fixture used to to mock brainstem library"""

    class MockSystem:
        """Class used to stub brainstem 'System'"""

        def __init__(self, **kwargs):
            pass

        getSerialNumber = mocker.MagicMock(return_value=Result(0, 0x1234))

    class MockUsb:
        """Class used to stub brainstem 'USB'"""

        def __init__(self, **kwargs):
            pass

        setPortEnable = mocker.MagicMock(return_value=Result.NO_ERROR)
        setPortDisable = mocker.MagicMock(return_value=Result.NO_ERROR)
        getPortCurrent = mocker.MagicMock(
            return_value=Result(0, int(1e6))  # 1 Ampere in micro Ampere
        )
        getPortVoltage = mocker.MagicMock(
            return_value=Result(0, int(1e6))  # 1 Volt in micro Volt
        )
        getPortCurrentLimit = mocker.MagicMock(
            return_value=Result(0, int(1e6))  # 1 Ampere in micro Ampere
        )
        setPortCurrentLimit = mocker.MagicMock(return_value=Result.NO_ERROR)

    class MockBrainstemUsb:
        """Class used to stub brainstem.stem.USBHub2x4 method"""

        def __init__(self, **kwargs):
            """"""
            pass

        disconnect = mocker.stub(name="disconnect")
        discoverAndConnect = mocker.MagicMock(return_value=Result.NO_ERROR)
        system = MockSystem()

        usb = MockUsb()

    mocker.patch.object(brainstem.stem, "USBHub2x4", new=MockBrainstemUsb)
    return brainstem.stem


@pytest.fixture()
def acron_aux():
    return AcronameAuxiliary()


def test_acroname_instance(mocker, mock_brainstem_usb, acron_aux):

    acron_aux._create_auxiliary_instance()

    mock_brainstem_usb.USBHub2x4.discoverAndConnect.assert_called_with(
        brainstem.link.Spec.USB, None
    )

    is_instantiated = acron_aux._create_auxiliary_instance()

    assert is_instantiated

    result = acron_aux._delete_auxiliary_instance()
    assert result


def test_acroname_create_nok(mocker, mock_brainstem_usb):

    mock_brainstem_usb.USBHub2x4.discoverAndConnect = mocker.MagicMock(
        return_value=Result.BUSY
    )
    acron_aux = AcronameAuxiliary("0x1234")
    acron_aux._create_auxiliary_instance()

    mock_brainstem_usb.USBHub2x4.discoverAndConnect.assert_called_with(
        brainstem.link.Spec.USB, 0x1234
    )

    is_instantiated = acron_aux._create_auxiliary_instance()

    assert not is_instantiated


def test_acroname_close_error(mock_brainstem_usb, acron_aux):

    mock_brainstem_usb.USBHub2x4.disconnect.side_effect = Exception("foo")

    acron_aux._delete_auxiliary_instance()
    mock_brainstem_usb.USBHub2x4.disconnect.assert_called_once()

    with pytest.raises(Exception) as excinfo:
        acron_aux._delete_auxiliary_instance()
        assert excinfo.value.message == "Unable to close the instrument."


def test_acroname_set_port(mocker, mock_brainstem_usb, acron_aux):

    result = acron_aux.set_port_enable(1)
    assert result == Result.NO_ERROR
    mock_brainstem_usb.USBHub2x4.usb.setPortEnable.assert_called_with(1)

    result = acron_aux.set_port_disable(2)
    assert result == Result.NO_ERROR
    mock_brainstem_usb.USBHub2x4.usb.setPortDisable.assert_called_with(2)

    mock_brainstem_usb.USBHub2x4.usb.setPortDisable = mocker.MagicMock(
        return_value=Result.BUSY
    )
    result = acron_aux.set_port_disable(0)
    assert result == Result.BUSY

    mock_brainstem_usb.USBHub2x4.usb.setPortEnable = mocker.MagicMock(
        return_value=Result.BUSY
    )
    result = acron_aux.set_port_enable(0)
    assert result == Result.BUSY


def test_acroname_get_port_current_voltage(mocker, mock_brainstem_usb, acron_aux):

    # Test current
    micro_amp = acron_aux.get_port_current(0, "uA")
    milli_amp = acron_aux.get_port_current(0, "mA")
    one_amp = acron_aux.get_port_current(0, "A")
    assert micro_amp == 1e6
    assert milli_amp == 1e3
    assert one_amp == 1

    micro_amp_limit = acron_aux.get_port_current_limit(0, "uA")
    milli_amp_limit = acron_aux.get_port_current_limit(0, "mA")
    one_amp_limit = acron_aux.get_port_current_limit(0, "A")
    assert micro_amp_limit == 1e6
    assert milli_amp_limit == 1e3
    assert one_amp_limit == 1

    # Test voltage
    micro_volt = acron_aux.get_port_voltage(0, "uV")
    milli_volt = acron_aux.get_port_voltage(0, "mV")
    one_volt = acron_aux.get_port_voltage(0, "V")
    assert micro_volt == 1e6
    assert milli_volt == 1e3
    assert one_volt == 1


def test_acroname_invalid_units(
    caplog,
    mocker,
    mock_brainstem_usb,
    acron_aux,
):

    with caplog.at_level(logging.ERROR):
        ultra_amp = acron_aux.get_port_current(0, "ultraA")

    assert "Unit 'ultraA' is not supported" in caplog.text
    assert ultra_amp == None

    with caplog.at_level(logging.ERROR):
        ultra_volt = acron_aux.get_port_voltage(0, "ultraV")

    assert "Unit 'ultraV' is not supported" in caplog.text
    assert ultra_volt == None

    with caplog.at_level(logging.ERROR):
        pico_amp = acron_aux.get_port_current_limit(0, "picoA")

    assert "Unit 'picoA' is not supported" in caplog.text
    assert pico_amp == None

    with caplog.at_level(logging.ERROR):
        acron_aux.set_port_current_limit(0, 1, "gigaA")

    assert "Unit 'gigaA' is not supported" in caplog.text


def test_acroname_set_port_limit(mocker, mock_brainstem_usb, acron_aux):

    # Test set current micro Ampere
    acron_aux.set_port_current_limit(0, 1, "uA")
    mock_brainstem_usb.USBHub2x4.usb.setPortCurrentLimit.assert_called_with(0, 1)

    # Test set current milli Ampere
    acron_aux.set_port_current_limit(0, 1, "mA")
    mock_brainstem_usb.USBHub2x4.usb.setPortCurrentLimit.assert_called_with(0, 1e3)

    # Test set current Ampere
    acron_aux.set_port_current_limit(0, 1, "A")
    mock_brainstem_usb.USBHub2x4.usb.setPortCurrentLimit.assert_called_with(0, 1e6)
