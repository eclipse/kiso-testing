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

import pytest

from pykiso.lib.connectors.cc_socket_can import socketcan_to_trc
from pykiso.lib.connectors.cc_socket_can.socketcan_to_trc import SocketCan2Trc, can


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
        importlib.reload(socketcan_to_trc)
    sys.modules["can"] = can
    importlib.reload(socketcan_to_trc)


@pytest.mark.parametrize(
    "logging_requested",
    [
        ("log.trc"),
        ("-"),
    ],
)
def test_constructor(mock_can_bus, mocker, logging_requested):
    CAN_NAME = "vcan0"
    LOG_FILE = logging_requested

    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")

    logger = SocketCan2Trc(CAN_NAME, LOG_FILE)
    assert logger.can_name == CAN_NAME
    assert logger.trc_file_name == LOG_FILE

    assert logger.trc_file == sys.stdout

    mock_thread.assert_called_once_with(CAN_NAME, bustype="socketcan", fd=True)
    mock_notifier.assert_called_once()


@pytest.fixture
def tmp_file(tmp_path):
    f = tmp_path / "log.trc"
    return f


def test_open_trc_file(mock_can_bus, mocker, tmp_file):
    CAN_NAME = "vcan0"
    LOG_FILE = tmp_file

    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")
    mock_open = mocker.patch("builtins.open")
    logger = SocketCan2Trc(CAN_NAME, LOG_FILE)

    logger.open_trc_file()
    mock_open.assert_called_with(LOG_FILE, mode="w", encoding="utf-8")

    logger = SocketCan2Trc(CAN_NAME, "-")

    logger.open_trc_file()
    mock_open.assert_called_once()
    assert logger.trc_file == sys.stdout


def test_get_ip_link_show(mocker):

    mock_run = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.socketcan_to_trc.subprocess.run"
    )
    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")

    mock_stdout = mocker.MagicMock()
    mock_stdout.configure_mock(
        **{"stdout.decode.return_value": "A\n    B\n    C", "returncode": 0}
    )

    mock_run.return_value = mock_stdout

    logger = SocketCan2Trc("vcan0", "-")
    ip_link_show = logger.get_ip_link_show()

    assert "A\n;" + " " * 45 + "B" in ip_link_show


def test_get_ip_link_show_exception(mocker):

    mock_run = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.socketcan_to_trc.subprocess.run"
    )
    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")

    mock_stdout = mocker.MagicMock()
    mock_stdout.configure_mock(
        **{"stdout.decode.return_value": "A\n    B\n    C", "returncode": 1}
    )

    mock_run.return_value = mock_stdout

    logger = SocketCan2Trc("vcan0", "-")
    with pytest.raises(RuntimeError) as excinfo:
        ip_link_show = logger.get_ip_link_show()

    assert "ip -d link show failed:" in str(excinfo)


def test_start(mocker, tmp_file):
    mock_run = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.socketcan_to_trc.subprocess.run"
    )
    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")

    mock_get_ip_link_show = mocker.patch.object(
        SocketCan2Trc, "get_ip_link_show", return_value="something"
    )

    logger = SocketCan2Trc("vcan0", str(tmp_file))

    logger.start()
    logger.trc_file.flush()
    last_header_line = ";---+-- ------+------ +- --+----- +- +- +- -- -- -- -- -- -- --"
    with open(tmp_file) as logfile:
        txt = logfile.read()
        assert last_header_line in txt
        assert "vcan0" in txt

    assert logger.started == True


def test_on_message_received(caplog, mocker, tmp_file):

    mock_run = mocker.patch(
        "pykiso.lib.connectors.cc_socket_can.socketcan_to_trc.subprocess.run"
    )
    mock_thread = mocker.patch("can.ThreadSafeBus")
    mock_notifier = mocker.patch("can.Notifier")

    mock_get_ip_link_show = mocker.patch.object(
        SocketCan2Trc, "get_ip_link_show", return_value="something"
    )

    mock_get_ip_link_show = mocker.patch.object(
        SocketCan2Trc, "get_start_time", return_value=10
    )

    logger = SocketCan2Trc("vcan0", str(tmp_file))
    logger.start()

    can_msg = can.Message(
        arbitration_id=100,
        data=bytes([1, 2, 3, 4, 5, 6, 10, 255]),
        is_extended_id=True,
        is_fd=True,
        bitrate_switch=True,
        timestamp=10,
    )

    for _ in range(10):
        logger.on_message_received(can_msg)

    with caplog.at_level(logging.INTERNAL_INFO):
        can_msg.is_error_frame = True
        logger.on_message_received(can_msg)

    assert "is errorframe" in caplog.text

    with open(tmp_file) as logfile:
        txt = logfile.read()
        assert "      9         0.000 FB     0064 RX 8  01 02 03 04 05 06 0A FF" in txt
        assert "ER     0064 RX 8  01 02 03 04 05 06 0A FF" in txt
        assert "     10" in txt
        assert "      9" in txt


@pytest.mark.parametrize(
    "is_remote_frame_value, is_error_frame_value, is_fd_value,bitrate_switch_value,error_state_indicator_value, expected_return",
    [
        (True, True, True, True, True, "RR"),
        (False, True, True, True, True, "ER"),
        (False, False, False, True, True, "DT"),
        (False, False, True, True, True, "BI"),
        (False, False, True, True, False, "FB"),
        (False, False, True, False, True, "FE"),
        (False, False, True, False, False, "FD"),
    ],
)
def test_get_type(
    is_remote_frame_value,
    is_error_frame_value,
    is_fd_value,
    bitrate_switch_value,
    error_state_indicator_value,
    expected_return,
):
    class access_static_method(SocketCan2Trc):
        def __init__(self):
            self.started = False

        def get_type(self, can_frame):
            return super().get_type(can_frame)

    can_msg = can.Message(
        is_remote_frame=is_remote_frame_value,
        is_error_frame=is_error_frame_value,
        is_fd=is_fd_value,
        bitrate_switch=bitrate_switch_value,
        error_state_indicator=error_state_indicator_value,
    )

    assert access_static_method().get_type(can_msg) == expected_return
