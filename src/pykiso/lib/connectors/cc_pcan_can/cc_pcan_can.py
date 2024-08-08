##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Can Communication Channel using PCAN hardware
*********************************************

:module: cc_pcan_can

:synopsis: CChannel implementation for CAN(fd) using PCAN API from python-can

.. currentmodule:: cc_pcan_can

"""
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

try:
    import can
    import can.bus
    import can.interfaces.pcan.basic as PCANBasic
    from can import TRCFileVersion
except ImportError as e:
    raise ImportError(f"{e.name} dependency missing, consider installing pykiso with 'pip install pykiso[can]'")

try:
    # use to avoid timestamp inconsistances between pykiso and python can
    import uptime

    if uptime.boottime() is None:
        boottime_epoch = 0
    else:
        boottime_epoch = uptime.boottime().timestamp()
except ImportError:
    boottime_epoch = 0

from pykiso import CChannel

from .trc_handler import TRCReaderCanFD, TRCWriterCanFD, TypedMessage

log = logging.getLogger(__name__)


class PcanFilter(logging.Filter):
    """Filter specific pcan logging messages"""

    def filter(self, record: logging.LogRecord) -> bool:
        """Determine if the specified record is to be logged. It will not if
        it is a pcan bus error message

        :param record: record of the event to filter if it is a pcan bus error

        :return: True if the record should be logged, or False otherwise.
        """
        return not record.getMessage().startswith("Bus error: an error counter")


class CCPCanCan(CChannel):
    """CAN FD channel-adapter."""

    def __init__(
        self,
        interface: str = "pcan",
        channel: str = "PCAN_USBBUS1",
        state: str = "ACTIVE",
        trace_path: str = "",
        trace_size: int = 10,
        bitrate: int = 500000,
        is_fd: bool = True,
        enable_brs: bool = False,
        f_clock_mhz: int = 80,
        nom_brp: int = 2,
        nom_tseg1: int = 63,
        nom_tseg2: int = 16,
        nom_sjw: int = 16,
        data_brp: int = 4,
        data_tseg1: int = 7,
        data_tseg2: int = 2,
        data_sjw: int = 2,
        is_extended_id: bool = False,
        remote_id: int = None,
        can_filters: list = None,
        logging_activated: bool = True,
        bus_error_warning_filter: bool = False,
        merge_trc_logs: bool = True,
        strategy_trc_file: Optional[Literal["testRun", "testCase"]] = None,
        **kwargs,
    ):
        """Initialize can channel settings.

        :param interface: python-can interface modules used
        :param channel: the can interface name
        :param state: BusState of the channel
        :param trace_path: path to write the trace (can be a folder or a .trc file)
            .. note:: If the .trc file already exists, it will be overwritten. If the trace_path
            is an existing folder, a default name will be generated for the trace file
            containing the timestamp. If the trace_path is a non-existent folder, the
            folder will be created and the default name will be used for the trace
            file. If the trace_path is not defined by the user, the default file will be
            saved in the current working directory.
        :param trace_size: maximum size of the trace (in MB)
        :param bitrate: Bitrate of channel in bit/s,ignored if using CanFD
        :param is_fd: Should the Bus be initialized in CAN-FD mode
        :param enable_brs: sets the bitrate_switch flag to use higher transmission speed
        :param f_clock_mhz:  Clock rate in MHz
        :param nom_brp: Clock prescaler for nominal time quantum
        :param nom_tseg1: Time segment 1 for nominal bit rate, that is,
            the number of quanta from the Sync Segment to the sampling point
        :param nom_tseg2: Time segment 2 for nominal bit rate,
            that is, the number of quanta from the sampling point to the end of the bit
        :param nom_sjw: Synchronization Jump Width for nominal bit rate.
            Decides the maximum number of time quanta that the controller
            can resynchronize every bit
        :param data_brp: Clock prescaler for fast data time quantum
        :param data_tseg1: Time segment 1 for fast data bit rate, that is,
            the number of quanta from the Sync Segment to the sampling point
        :param data_tseg2: Time segment 2 for fast data bit rate, that is,
            the number of quanta from the sampling point to the end of the bit.
            In the range (1..16)
        :param data_sjw: Synchronization Jump Width for fast data bit rate
        :param is_extended_id: This flag controls the size of the arbitration_id field
        :param remote_id: id used for transmission
        :param can_filters: iterable used to filter can id on reception
        :param logging_activated: boolean used to disable logfile creation
        :param bus_error_warning_filter: if True filter the PCAN driver warnings
            'Bus error: an error counter' from the logs.
        :param merge_trc_logs: if True, merge all traces in one file at the end of the program
        :param strategy_trc_file: Strategy for the trace file by default (set to None) it will
            be one trace file for all the tests run, if set to 'test' it will be one trace file
            per test run and 'testCase' it will be one trace file per testCase.
        """
        super().__init__(**kwargs)
        self.interface = interface
        self.channel = channel
        self.state = can.bus.BusState[state.upper()]
        self.trace_path = Path(trace_path)
        self.trace_size = trace_size
        self.bitrate = bitrate
        self.is_fd = is_fd
        self.enable_brs = enable_brs
        self.f_clock_mhz = f_clock_mhz
        self.nom_brp = nom_brp
        self.nom_tseg1 = nom_tseg1
        self.nom_tseg2 = nom_tseg2
        self.nom_sjw = nom_sjw
        self.data_brp = data_brp
        self.data_tseg1 = data_tseg1
        self.data_tseg2 = data_tseg2
        self.data_sjw = data_sjw
        self.is_extended_id = is_extended_id
        self.remote_id = remote_id
        self.can_filters = can_filters
        self.bus = None
        self.logging_activated = logging_activated
        self.raw_pcan_interface = None
        self.strategy_trc_file = strategy_trc_file
        # Set a timeout to send the signal to the GIL to change thread.
        # In case of a multi-threading system, all tasks will be called one after the other.
        self.timeout = 1e-6
        self.trc_count = 0
        self.boottime_epoch = boottime_epoch
        self._initialize_trace()
        self.merge_trc_logs = merge_trc_logs if strategy_trc_file is None else False
        self._trc_file_names: dict[Path, str | None] = {}
        self.trace_running = False
        if bus_error_warning_filter:
            logging.getLogger("can.pcan").addFilter(PcanFilter())

        if self.enable_brs and not self.is_fd:
            log.internal_warning("Bitrate switch will have no effect because option is_fd is set to false.")

    def _initialize_trace(self) -> None:
        """Initialize the trace path and check its size

        :raises ValueError: if the trace_path is a file but not a trc file
        """
        # Handle trace path and name
        if self.trace_path.suffix == ".trc":
            self.trace_name = self.trace_path.name
            self.trace_path = self.trace_path.parent
        elif self.trace_path and self.trace_path.suffix == "":
            self.trace_name = None
        elif not self.trace_path:
            self.trace_path = Path.cwd()
            self.trace_name = None
        elif self.trace_path.suffix not in [".trc", ""]:
            raise ValueError(f"Trace name {self.trace_path.name} is incorrect, it should be a trc file")

        # Check trace size
        if not 0 < self.trace_size <= 100:
            self.trace_size = 10
            log.internal_warning(
                "Make sure trace size is between 1 and 100 Mb. Setting trace size to default value "
                f"value : {self.trace_size}."
            )

    def _cc_open(self) -> None:
        """Open a can bus channel, set filters for reception and activate PCAN log."""
        self.bus = can.interface.Bus(
            interface=self.interface,
            channel=self.channel,
            state=self.state,
            bitrate=self.bitrate,
            fd=self.is_fd,
            f_clock_mhz=self.f_clock_mhz,
            nom_brp=self.nom_brp,
            nom_tseg1=self.nom_tseg1,
            nom_tseg2=self.nom_tseg2,
            nom_sjw=self.nom_sjw,
            data_brp=self.data_brp,
            data_tseg1=self.data_tseg1,
            data_tseg2=self.data_tseg2,
            data_sjw=self.data_sjw,
            can_filters=self.can_filters,
        )

        if self.logging_activated and self.raw_pcan_interface is None:
            self.raw_pcan_interface = PCANBasic.PCANBasic()
            if self.strategy_trc_file is None:
                self._pcan_configure_trace()

    def _pcan_configure_trace(self) -> None:
        """Configure PCAN dongle to create a trace file.

        If self.trace_path is set, this path will be created, if it does not
        exist and the logfile will be placed there.
        Otherwise it will be logged to the current working directory if a
        default filename, which will be overwritten in successive calls.
        If an error occurs, the trace will not be started and the error logged.
        No exception is thrown in this case.
        """
        pcan_channel = getattr(PCANBasic, self.channel)
        if self.trace_path is None:
            log.internal_warning("No trace path specified, an existing trace will be overwritten.")
            pcan_path_argument = PCANBasic.TRACE_FILE_OVERWRITE
        else:
            pcan_path_argument = PCANBasic.TRACE_FILE_DATE | PCANBasic.TRACE_FILE_TIME

        try:
            if self.trace_path is not None:
                if not Path(self.trace_path).exists():
                    Path(self.trace_path).mkdir(parents=True, exist_ok=True)
                    log.internal_info("Path %s created", self.trace_path)
                self._pcan_set_value(
                    pcan_channel,
                    PCANBasic.PCAN_TRACE_LOCATION,
                    bytes(self.trace_path),
                )
                log.internal_info(
                    "Tracefile path in PCAN device configured to %s",
                    self.trace_path,
                )

            if sys.platform != "darwin":
                log.internal_info("Segmented option of trace file activated.")
                self._pcan_set_value(
                    pcan_channel,
                    PCANBasic.TRACE_FILE_SEGMENTED,
                    PCANBasic.PCAN_PARAMETER_ON,
                )

                if self.trace_size != 10:
                    log.internal_info("Trace size set to %d MB.", self.trace_size)
                    self._pcan_set_value(
                        pcan_channel,
                        PCANBasic.PCAN_TRACE_SIZE,
                        self.trace_size,
                    )
            else:
                log.internal_warning("TRACE_FILE_SEGMENTED deactivated for macos!")

            self._pcan_set_value(
                pcan_channel,
                PCANBasic.PCAN_TRACE_CONFIGURE,
                pcan_path_argument,
            )
            log.internal_info("Tracefile configured")

            self._pcan_set_value(
                pcan_channel,
                PCANBasic.PCAN_TRACE_STATUS,
                PCANBasic.PCAN_PARAMETER_ON,
            )
            self.trace_running = True
            log.internal_info("Trace activated")
            # Add the file name and trace path to rename them later
            if self._trc_file_names.get(self.trace_path, None) is None:
                self._trc_file_names[self.trace_path] = []
            self._trc_file_names[self.trace_path].append(self.trace_name)
            self.trc_count += 1
        except RuntimeError:
            log.error(f"Logging for {self.channel} not activated")
        except OSError as e:
            log.error(f"Can not create log folder for PCAN logs: {e}")
            log.error(f"Logging for {self.channel} not activated")

    def _pcan_set_value(self, channel, parameter, buffer) -> None:
        """Set a value in the PCAN api.

        If this is not successful, a RuntimeError is returned, as well as the
        PCAN error text is logged, if possible.

        :param channel: Channel for PCANBasic.SetValue
        :param parameter: Parameter for PCANBasic.SetValue
        :param buffer: Buffer for PCANBasic.SetValue

        :raises RuntimeError: Raised if the function is not successful
        """
        try:
            result = self.raw_pcan_interface.SetValue(
                channel,
                parameter,
                buffer,
            )
        except Exception as e:
            log.error(f"Exception in call to SetValue: {e}")
            raise RuntimeError("Error configuring logging on PCAN")
        else:
            if result != PCANBasic.PCAN_ERROR_OK:
                _, error_msg = self.raw_pcan_interface.GetErrorText(result)
                log.error(error_msg)
                raise RuntimeError(f"Error configuring logging on PCAN: {result}")

    def _cc_close(self) -> None:
        """Close the current can bus channel and uninitialize PCAN handle."""
        self.stop_pcan_trace()
        self.bus.shutdown()
        self.bus = None
        if self.logging_activated:
            try:
                result = self.raw_pcan_interface.Uninitialize(PCANBasic.PCAN_NONEBUS)
            except Exception as e:
                log.exception(f"Error in call to Uninitialize: {e}")
            else:
                if result != PCANBasic.PCAN_ERROR_OK:
                    _, error_msg = self.raw_pcan_interface.GetErrorText(result)
                    log.error(error_msg)
            finally:
                self.raw_pcan_interface = None

    def _cc_send(self, msg: bytes, remote_id: Optional[int] = None, **kwargs) -> None:
        """Send a CAN message at the configured id.

        If remote_id parameter is not given take configured ones

        :param msg: data to send
        :param remote_id: destination can id used
        :param kwargs: named arguments
        """

        remote_id = remote_id or self.remote_id

        can_msg = can.Message(
            arbitration_id=remote_id,
            data=msg,
            is_extended_id=self.is_extended_id,
            is_fd=self.is_fd,
            bitrate_switch=self.enable_brs,
        )
        self.bus.send(can_msg)

        log.internal_debug("%s sent CAN Message: %s, data: %s", self, can_msg, msg)

    def _cc_receive(self, timeout: float = 0.0001) -> Dict[str, Union[bytes, int, None]]:
        """Receive a can message using configured filters.

        :param timeout: timeout applied on reception

        :return: the received data and the source can id
        """
        try:  # Catch bus errors & rcv.data errors when no messages where received
            received_msg = self.bus.recv(timeout=timeout or self.timeout)

            if received_msg is not None:
                frame_id = received_msg.arbitration_id
                payload = received_msg.data
                timestamp = received_msg.timestamp - self.boottime_epoch

                log.internal_debug(
                    "received CAN Message: %s, %s, %s",
                    frame_id,
                    payload,
                    timestamp,
                )
                return {
                    "msg": payload,
                    "remote_id": frame_id,
                    "timestamp": timestamp,
                }
            else:
                return {"msg": None}
        except can.CanError as can_error:
            log.internal_info("encountered CAN error while receiving message: %s", can_error)
            return {"msg": None}
        except Exception:
            log.exception(f"encountered error while receiving message via {self}")
            return {"msg": None}

    @staticmethod
    def _extract_header(trace: Path) -> str:
        """Extract data from trc file header

        :param trace: trc file from which to extract the data

        :return: header data
        """
        header_data = ""

        with trace.open("r") as trc:
            data = trc.read().splitlines(True)
            for line in data:
                if line.startswith(";"):
                    header_data += line
                else:
                    break
        return header_data

    def _merge_trc(self) -> None:
        """Merge all traces file in one and fix potential inconsistencies."""

        list_of_traces = []
        first_trace_name = None
        first_trace_path = None

        for trace_path, trace_file_names in self._trc_file_names.items():
            if isinstance(trace_path, str):
                trace_path = Path(trace_path)
            if first_trace_path is None:
                first_trace_name = trace_file_names[0]
                first_trace_path = trace_path
            # Get all the trace files created in a list
            list_of_traces.extend(sorted(trace_path.glob("*.trc"), key=os.path.getmtime)[-len(trace_file_names) :])

        try:
            if first_trace_name is None:
                # If a log file is not provided, merge everything into the first created trace
                result_trace = list_of_traces[0]
            else:
                # Otherwise create a separate file
                result_trace = Path(first_trace_path / first_trace_name)
                # replace the first trace with the result trace in the trace list
                # to ensure that all traces except the merged trace are deleted in _read_trace_messages
                list_of_traces[0] = Path(shutil.move(str(list_of_traces[0]), str(result_trace)))

            # Extract header
            header_data = CCPCanCan._extract_header(list_of_traces[0])

            # Get messages from all traces
            try:
                messages = self._read_trace_messages(list_of_traces, result_trace)
            except ValueError:
                return

            # Write header in result trace
            result_trace.write_text(header_data)

            # Write all messages in result trace
            with TRCWriterCanFD(result_trace) as writer:
                writer.file_version = self.trc_file_version
                log.internal_debug("TRC file version is %s", self.trc_file_version)
                writer.header_data = header_data
                for msg in messages:
                    writer.on_message_received(msg, self.trc_start_time.timestamp())

        except IndexError:
            log.internal_warning("No trace to merge")

    def _read_trace_messages(self, list_of_traces: List[Path], result_trace: Path) -> List[TypedMessage]:
        """Get the list of messages for all traces with corrected offset

        :param list_of_traces: list of all traces
        :param result_trace: trace where to merge

        :return: list of corrected typed messages from all traces
        """
        messages = []
        for trc in list_of_traces:
            log.internal_debug("Merging trace %s into %s", trc.name, result_trace.name)
            with TRCReaderCanFD(trc) as reader:
                current_trc_messages = list(reader)

                if trc == result_trace:
                    # Get info for the first trace
                    self.trc_start_time = reader.start_time
                    self.trc_file_version = reader.file_version
                else:
                    # Get offset in milliseconds
                    current_trc_start_time = reader.start_time
                    offset = (current_trc_start_time - self.trc_start_time).total_seconds()
                    current_trc_messages = CCPCanCan._remove_offset(current_trc_messages, offset)
                    os.remove(trc)
                if self.trc_file_version in [
                    TRCFileVersion.V1_1,
                    TRCFileVersion.V1_2,
                    TRCFileVersion.V1_3,
                ]:
                    log.warning(
                        "Trace merging is not available for trc file version %s",
                        self.trc_file_version,
                    )
                    raise ValueError
                messages += current_trc_messages
        return messages

    @staticmethod
    def _remove_offset(messages: List[TypedMessage], offset: float) -> List[TypedMessage]:
        """Remove offset to the timestamp of a list of messages

        :param messages: list of messages to adapt
        :param offset: offset to add in seconds

        :return: List of message with corrected timestamps
        """
        for msg in messages:
            msg.timestamp = msg.timestamp + offset
        return messages

    def _rename_trc(self):
        """Rename the trace file created if a name has been specified"""
        for trace_path, trace_file_names in self._trc_file_names.items():
            list_of_traces = sorted(trace_path.glob("*.trc"), key=os.path.getmtime)[-len(trace_file_names) :]
            for index, file_name in enumerate(trace_file_names):
                if file_name is not None:
                    list_of_traces[index].rename(trace_path / file_name)

    def shutdown(self) -> None:
        """Destructor method."""
        if not self.logging_activated:
            return
        if self.merge_trc_logs:
            self._merge_trc()
        else:
            self._rename_trc()

    def stop_pcan_trace(self):
        """
        Stops the PCAN trace if it is currently running.
        :return: None
        """
        if not self.logging_activated:
            return
        if not self.trace_running:
            log.warning("Trace is already stopped")
            return

        pcan_channel = getattr(PCANBasic, self.channel)
        self._pcan_set_value(
            pcan_channel,
            PCANBasic.PCAN_TRACE_STATUS,
            PCANBasic.PCAN_PARAMETER_OFF,
        )
        self.trace_running = False

    def start_pcan_trace(self, trace_path: Optional[str] = None, trace_size: int = None) -> None:
        """Start the PCAN trace, the trace file will be renamed after the pcan trace will be stopped.

        :param trace_path: Trace path where the trace should be written if None is given it will use
            the trace path defined for the last trace created, defaults to None
        :param trace_size:  maximum size of the trace (in MB), defaults to None
        """
        if not self.logging_activated:
            log.warning("Logging is not activated")
            return
        if self.trace_running:
            log.warning("Trace is already started")
            return

        self.trace_size = trace_size or self.trace_size
        self.trace_path = Path(trace_path) if trace_path else self.trace_path
        self._initialize_trace()
        self._pcan_configure_trace()
