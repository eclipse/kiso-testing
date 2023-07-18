##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
TRC file handler based on Python CAN
************************************

:module: trc_handler

:synopsis: Additional layer for python-can trc reader and write to handle can FD

.. currentmodule:: trc_handler

"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta

try:
    from can.io.trc import TRCFileVersion, TRCReader, TRCWriter
    from can.util import channel2int, dlc2len, len2dlc
    from can import Message
except ImportError as e:
    raise ImportError(
        f"{e.name} dependency missing, consider installing pykiso with 'pip install pykiso[can]'"
    )


log = logging.getLogger(__name__)


class TypedMessage(Message):
    """Message with type attribut added and that can handle empty arbitration id.
    Necessary because python-can does not handle types from CAN FD and informations
    contained in Message are not enough to deduce it.
    Some of those types (ex: ST) also have no arbitration id which cannot be handle by
    python-can Message object.
    """

    def __init__(self, type: str, msg: Message):
        """Create a typed message

        :param type: type of CAN messahe (ex:DT)
        :param msg: python-can message from which to create the typed message
        """
        super().__init__()
        self.type = type
        self.timestamp = msg.timestamp
        self.arbitration_id = msg.arbitration_id
        self.is_extended_id = msg.is_extended_id
        self.is_remote_frame = msg.is_remote_frame
        self.is_error_frame = msg.is_error_frame
        self.channel = msg.channel
        self.dlc = msg.dlc
        self.data = msg.data
        self.is_fd = msg.is_fd
        self.is_rx = msg.is_rx
        self.bitrate_switch = msg.bitrate_switch
        self.error_state_indicator = msg.error_state_indicator
        self._check = msg._check

    def __repr__(self) -> str:
        """String representation that can handle messages with no arbitration id

        return: string representation of the message"""
        if self.type not in ["EC", "ER", "ST"]:
            args = [
                f"timestamp={self.timestamp}",
                f"arbitration_id={self.arbitration_id:#x}",
                f"is_extended_id={self.is_extended_id}",
            ]
        else:
            args = [
                f"timestamp={self.timestamp}",
                f"arbitration_id={self.arbitration_id}",
                f"is_extended_id={self.is_extended_id}",
            ]

        if not self.is_rx:
            args.append("is_rx=False")

        if self.is_remote_frame:
            args.append(f"is_remote_frame={self.is_remote_frame}")

        if self.is_error_frame:
            args.append(f"is_error_frame={self.is_error_frame}")

        if self.channel is not None:
            args.append(f"channel={self.channel!r}")

        data = [f"{byte:#02x}" for byte in self.data]
        args += [f"dlc={self.dlc}", f"data=[{', '.join(data)}]"]

        if self.is_fd:
            args.append("is_fd=True")
            args.append(f"bitrate_switch={self.bitrate_switch}")
            args.append(f"error_state_indicator={self.error_state_indicator}")

        return f"can.Message({', '.join(args)})"


class TRCReaderCanFD(TRCReader):
    """Parse trc file to extract messages informations
    Unlike the base TRCReader class, also retrieve message type
    """

    def _nomalize_cols(self, cols: dict) -> dict:
        """Insert missing columns for specific messages (Hardware Status, Error Frames
        and Error Counter Changes) to avoid

        :param cols: message informations with missing columns

        :return: normalized message
        """
        type_ = cols[self.columns["T"]]
        if type_ in ["EC", "ER", "ST"]:
            if self.file_version == TRCFileVersion.V2_0:
                cols.insert(self.columns["I"], "    ")
            else:
                cols.insert(self.columns["I"], "   -")
            if "l" in self.columns:
                cols.insert(self.columns["l"], " ")
            if "L" in self.columns:
                cols.insert(self.columns["L"], " ")
        return cols

    def _parse_cols_V2_x(self, cols: List[str]) -> Optional[TypedMessage]:
        """Parse columns for file version 2.0 and 2.1.

        :param cols: list of columns to parse

        :return: typed message or None if message type is not supported
        """
        dtype = cols[self.columns["T"]]
        cols = self._nomalize_cols(cols)

        if dtype in ["DT", "FD", "FB", "EC", "ER", "ST"]:
            return self._parse_msg_V2_x(cols)
        else:
            log.info("TRCReader: Unsupported type '%s'", dtype)
            return None

    def _parse_msg_V2_x(self, cols: List[str]) -> Optional[Message]:
        """Parse messages for file version 2.0 and 2.1.

        :param cols: list of columns to parse

        return: typed message
        """
        type_ = cols[self.columns["T"]]
        bus = self.columns.get("B", None)

        # For 2.0 ST / ER and EC messages dlc and length are not in the trace but length is fixed
        if type_ in ["EC", "ER", "ST"] and self.file_version == TRCFileVersion.V2_0:
            if type_ == "ST":
                length = 4
            elif type_ == "ER":
                length = 5
            else:
                length = 2
            dlc = len2dlc(length)
        else:
            if "l" in self.columns:
                length = int(cols[self.columns["l"]])
                dlc = len2dlc(length)
            elif "L" in self.columns:
                dlc = int(cols[self.columns["L"]])
                length = dlc2len(dlc)
            else:
                raise ValueError("No length/dlc columns present.")

        msg = Message()
        if isinstance(self.start_time, datetime):
            msg.timestamp = (
                self.start_time + timedelta(milliseconds=float(cols[self.columns["O"]]))
            ).timestamp()
        else:
            msg.timestamp = float(cols[1]) / 1000

        if type_ not in ["EC", "ER", "ST"]:
            msg.arbitration_id = int(cols[self.columns["I"]], 16)
            msg.is_extended_id = len(cols[self.columns["I"]]) > 4
        # No arbitration id for ST / ER and EC messages
        else:
            msg.arbitration_id = cols[self.columns["I"]]
            msg.is_extended_id = False

        msg.channel = int(cols[bus]) if bus is not None else 1
        msg.dlc = dlc
        msg.data = bytearray(
            [int(cols[i + self.columns["D"]], 16) for i in range(length)]
        )
        msg.is_rx = cols[self.columns["d"]] == "Rx"
        msg.is_fd = type_ in ["FD", "FB", "FE", "BI"]
        msg.bitrate_switch = type_ in ["FB", " FE"]
        msg.error_state_indicator = type_ in ["FE", "BI"]
        msg.is_error_frame = type_ == "ER"
        msg.is_remote_frame = type_ == "RR"

        return TypedMessage(type_, msg)


class TRCWriterCanFD(TRCWriter):
    """Logs CAN FD data to text file (.trc)"""

    # Type has been added to FORMAT_MESSAGE >= 2.0
    FORMAT_MESSAGE_V2_1 = "{msgnr:>7} {time:13.3f} {type:>2} {channel:>2} {id:>8} {dir:>2} -  {dlc:<4} {data}"

    FORMAT_MESSAGE_V2_0 = (
        "{msgnr:>7} {time:13.3f} {type:>2} {id:>8} {dir:>2}  {dlc:<2} {data}"
    )

    def _format_message_init(self, msg: TypedMessage, channel: int) -> str:
        """Pick message format from file version and format initial message

        :return: message informations formated in a string
        """
        # Fix error from python can -> message number should start at one not zero
        self.msgnr = 1

        if self.file_version == TRCFileVersion.V1_0:
            self._msg_fmt_string = self.FORMAT_MESSAGE_V1_0
            self._format_message = self._format_message_by_format
        elif self.file_version == TRCFileVersion.V2_0:
            self._msg_fmt_string = self.FORMAT_MESSAGE_V2_0
            self._format_message = self._format_message_by_format
            return self._format_message_by_format(msg, channel)
        elif self.file_version == TRCFileVersion.V2_1:
            self._msg_fmt_string = self.FORMAT_MESSAGE_V2_1
            self._format_message = self._format_message_by_format
        else:
            raise NotImplementedError("File format is not supported")

    def _format_message_by_format(self, msg: TypedMessage, channel: int):
        """Format messages

        :return: message informations formated in a string
        """
        if msg.type not in ["EC", "ER", "ST"]:
            if msg.is_extended_id:
                arb_id = f"{msg.arbitration_id:07X}"
            else:
                arb_id = f"{msg.arbitration_id:04X}"
        else:
            arb_id = f"{msg.arbitration_id}"
        data = [f"{byte:02X}" for byte in msg.data]

        """For the time python-can was doing substraction with the first message timestamp
        which is incorrect. It should be with the start time of the trace otherwise the 
        first message will always have an offset of zero."""
        if self.file_version == TRCFileVersion.V1_0:
            serialized = self._msg_fmt_string.format(
                msgnr=self.msgnr,
                time=(msg.timestamp - self.first_timestamp) * 1000,
                channel=channel,
                id=arb_id,
                dir="Rx" if msg.is_rx else "Tx",
                dlc=msg.dlc,
                data=" ".join(data),
            )
        else:
            serialized = self._msg_fmt_string.format(
                msgnr=self.msgnr,
                time=(msg.timestamp - self.first_timestamp) * 1000,
                type=msg.type,
                channel=channel,
                id=arb_id,
                dir="Rx" if msg.is_rx else "Tx",
                dlc=msg.dlc,
                data=" ".join(data),
            )
        return serialized

    def set_header_data(self, header_data: List[str]):
        """Get all header info so trc writter can write it when needed

        :param header_data: list of all header lines
        """
        self.header_data = header_data

    def write_header(self, timestamp: float) -> None:
        """Modified write header that just write previously given header data

        :param timestamp: unused parameter kept to avoid breaking changes
        """
        if self.file_version in [
            TRCFileVersion.V1_0,
            TRCFileVersion.V2_0,
            TRCFileVersion.V2_1,
        ]:
            self.file.writelines(line for line in self.header_data)
        else:
            raise NotImplementedError("File format is not supported")
        self.header_written = True

    def on_message_received(self, msg: TypedMessage, trace_start_time: float) -> None:
        """Log a message in the trace. Handles CAN FD.

        In python can the reference is the timestamp of the first message (the first
        message offset is always zero), to fix this we take the begining of the trace.

        :param msg: typed message to log
        :param trace_start_time: timestamp of the start of the trace
        """

        if self.first_timestamp is None:
            self.first_timestamp = trace_start_time

        channel = channel2int(msg.channel)
        if channel is None:
            channel = self.channel
        else:
            # Many interfaces start channel numbering at 0 which is invalid
            channel += 1
        serialized = self._format_message(msg, channel)
        self.msgnr += 1
        self.log_event(serialized, msg.timestamp)
