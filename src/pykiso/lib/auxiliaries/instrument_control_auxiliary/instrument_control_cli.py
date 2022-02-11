##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Instrument Control CLI
**********************

:module: instrument_control_cli

:synopsis: Command Line Interface used to communicate with an instrument using the SCPI protocol.

.. currentmodule:: instrument_control_cli

"""
import enum
import logging
import sys

import click

from pykiso import __version__
from pykiso.lib.auxiliaries.instrument_control_auxiliary import (
    InstrumentControlAuxiliary,
)
from pykiso.lib.connectors.cc_tcp_ip import CCTcpip
from pykiso.lib.connectors.cc_visa import VISASerial, VISATcpip

from . import REGISTERED_INSTRUMENTS


@enum.unique
class ExitCode(enum.IntEnum):
    """List of possible exit codes"""

    SUCCESS = 0
    INTERFACE_NOT_PROVIDED = 1
    INSTRUMENT_OPENING_FAILED = 2


@enum.unique
class Interface(enum.Enum):
    """List of available interfaces"""

    VISA_SERIAL = "VISA_SERIAL"
    VISA_TCPIP = "VISA_TCPIP"
    SOCKET_TCPIP = "SOCKET_TCPIP"


def perform_actions(instr_aux: InstrumentControlAuxiliary, actions: dict) -> None:
    """Performs the desired actions from the CLI arguments

    :param instr_aux: instrument on which to perform the actions
    :param actions: dictionary containing the parsed argument and the corresponding value.
    """

    actions_dict = {
        # Instrument methods
        "write": {
            "text": "Custom write command",
            "set": instr_aux.write,
        },
        "query": {
            "text": "Custom query command",
            "set": instr_aux.query,
        },
        # General
        "identification": {
            "text": "Instrument identification",
            "get": instr_aux.helpers.get_identification,
        },
        "reset": {
            "text": "Resetting the instrument",
            "set": instr_aux.helpers.reset,
        },
        "status_byte": {
            "text": "Instrument's status byte",
            "get": instr_aux.helpers.get_status_byte,
        },
        "all_errors": {
            "text": "Instrument's all errors",
            "get": instr_aux.helpers.get_all_errors,
        },
        "self_test": {
            "text": "Performing a self test on the instrument",
            "get": instr_aux.helpers.self_test,
        },
        # Remote control
        "remote_control": {
            "text": "Instrument's remote control state",
            "get": instr_aux.helpers.get_remote_control_state,
            "set": instr_aux.helpers.set_remote_control_on,
            "unset": instr_aux.helpers.set_remote_control_off,
        },
        # Output mode
        "output_mode": {
            "text": "Instrument's output mode",
            "get": instr_aux.helpers.get_output_state,
            "set": instr_aux.helpers.enable_output,
            "unset": instr_aux.helpers.disable_output,
        },
        # Output channel
        "output_channel": {
            "text": "Instrument's output channel",
            "get": instr_aux.helpers.get_output_channel,
            "set": instr_aux.helpers.set_output_channel,
            "payload_type": "INT",
        },
        # Nominal values
        "voltage_nominal": {
            "text": "Instrument's nominal voltage (V)",
            "get": instr_aux.helpers.get_nominal_voltage,
        },
        "current_nominal": {
            "text": "Instrument's nominal current (A)",
            "get": instr_aux.helpers.get_nominal_current,
        },
        "power_nominal": {
            "text": "Instrument's nominal power (W)",
            "get": instr_aux.helpers.get_nominal_power,
        },
        # Target values
        "voltage_target": {
            "text": "Instrument's target voltage (V)",
            "get": instr_aux.helpers.get_target_voltage,
            "set": instr_aux.helpers.set_target_voltage,
        },
        "current_target": {
            "text": "Instrument's target current (A)",
            "get": instr_aux.helpers.get_target_current,
            "set": instr_aux.helpers.set_target_current,
        },
        "power_target": {
            "text": "Instrument's target power (W)",
            "get": instr_aux.helpers.get_target_power,
            "set": instr_aux.helpers.set_target_power,
        },
        # Measurements
        "voltage_measure": {
            "text": "Voltage measured on the instrument (V)",
            "get": instr_aux.helpers.measure_voltage,
        },
        "current_measure": {
            "text": "Current measured on the instrument (A)",
            "get": instr_aux.helpers.measure_current,
        },
        "power_measure": {
            "text": "Power measured on the instrument (W)",
            "get": instr_aux.helpers.measure_power,
        },
        # Limit values
        "voltage_limit_low": {
            "text": "Instrument's voltage lower limit (V)",
            "get": instr_aux.helpers.get_voltage_limit_low,
            "set": instr_aux.helpers.set_voltage_limit_low,
        },
        "voltage_limit_high": {
            "text": "Instrument's voltage higher limit (V)",
            "get": instr_aux.helpers.get_voltage_limit_high,
            "set": instr_aux.helpers.set_voltage_limit_high,
        },
        "current_limit_low": {
            "text": "Instrument's current lower limit (A)",
            "get": instr_aux.helpers.get_current_limit_low,
            "set": instr_aux.helpers.set_current_limit_low,
        },
        "current_limit_high": {
            "text": "Instrument's current higher limit (A)",
            "get": instr_aux.helpers.get_current_limit_high,
            "set": instr_aux.helpers.set_current_limit_high,
        },
        "power_limit_high": {
            "text": "Instrument's power higher limit (W)",
            "get": instr_aux.helpers.get_power_limit_high,
            "set": instr_aux.helpers.set_power_limit_high,
        },
    }
    for arg, value in actions.items():
        # use registered command from the SCPI library
        if isinstance(arg, str) and arg in actions_dict.keys():
            try:
                # check if string provided value can be converted into a float
                # for commands which payload can be a tag (get) or a float value to set
                # and in interactive mode
                float(value)
                # if successful, see if the command needs an float (default) or an int
                if (
                    "payload_type" in actions_dict[arg]
                    and actions_dict[arg]["payload_type"] == "INT"
                ):
                    logging.info(
                        f"{actions_dict[arg]['text']}: {actions_dict[arg]['set'](int(value))}"
                    )
                else:
                    logging.info(
                        f"{actions_dict[arg]['text']}: {actions_dict[arg]['set'](float(value))}"
                    )
            except TypeError:
                # occurs when value is None
                pass
            except ValueError:
                # provided value is a tag
                if str(value).upper() == "GET":
                    logging.info(
                        f"{actions_dict[arg]['text']}: {actions_dict[arg]['get']()}"
                    )
                elif str(value).upper() in "SET ON ENABLE".split():
                    logging.info(
                        f"{actions_dict[arg]['text']}: {actions_dict[arg]['set']()}"
                    )
                elif str(value).upper() in "UNSET OFF DISABLE".split():
                    logging.info(
                        f"{actions_dict[arg]['text']}: {actions_dict[arg]['unset']()}"
                    )
                elif value is None:
                    # no value was provided
                    pass
                else:
                    # provided value is not valid
                    logging.warning(
                        f"{value} is not a valid parameter for {arg}, please try again."
                    )
        else:
            logging.warning("Command not found, please try again.")


def setup_interface(
    interface: str,
    baud_rate: int = None,
    ip_address: str = None,
    port: int = None,
    protocol: str = None,
    name: str = None,
) -> InstrumentControlAuxiliary:
    """Set up the instrument auxiliary with the appropriate interface settings.
    The ip address must be provided in the case of TCPIP interfaces, as must
    the serial port for VISA_SERIAL interface. The baud rate and the output channel
    to use are optional.

    :param interface: interface to use
    :param baud_rate: baud rate to use
    :param ip_address: ip address of the remote instrument (used for remote control only)
    :param port: the port of the device to connect to. This is either a serial port for
        a VISA_SERIAL interface or an IP port in case of an TCPIP interfaces.
    :param protocol: The protocol to use for VISA_TCPIP interfaces.
    :param name: instrument name used to adapt the SCPI commands to be sent to the instrument

    :return: The created instrument auxiliary.
    """
    if interface == Interface.VISA_TCPIP.value:
        if ip_address is None:
            logging.error("An IP address must be provided!")
            raise ConnectionAbortedError()
        else:
            port = f"::{port}" if port else ""
            com_channel = VISATcpip(ip_address=ip_address + port, protocol=protocol)
    elif interface == Interface.VISA_SERIAL.value:
        if port is None:
            logging.error("A serial port must be provided!")
            raise ConnectionAbortedError()
        else:
            com_channel = VISASerial(serial_port=port, baud_rate=baud_rate)
    elif interface == Interface.SOCKET_TCPIP.value:
        if ip_address is None or port is None:
            logging.error("You must provide an IP address and a port (usually 5025).")
            raise ConnectionAbortedError()
        else:
            com_channel = CCTcpip(dest_ip=ip_address, dest_port=port)
    else:
        logging.error("You must choose an interface! Available interfaces are:")
        for interface in Interface:
            logging.error(interface.value)
        raise ConnectionAbortedError()

    instr_aux = InstrumentControlAuxiliary(com=com_channel, instrument=name)
    instr_aux.create_instance()
    return instr_aux


def initialize_logging(log_level: str) -> logging.getLogger:
    """Initialize the logging by setting the general log level

    :param log_level: any of DEBUG, INFO, WARNING, ERROR
    :returns: configured Logger
    """
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    kwargs = {
        "level": levels[log_level],
    }
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        **kwargs,
    )
    return logging.getLogger(__name__)


def parse_user_command(user_cmd: str) -> dict:
    """Parses the command from user input in interactive mode

    :param user_cmd: command provided by the user in interactive mode
    :return: a single-item dictionary containing the parsed command as
        key the the corresponding payload as value"""
    cmd = user_cmd.replace("-", "_").replace("__", "").split()
    if len(cmd) == 1:
        return {cmd[0]: "get"}
    else:
        return {cmd[0]: cmd[1]}


@click.command()
@click.option(
    "-b",
    "--baud-rate",
    required=False,
    default=9600,
    type=click.INT,
    help="The value to set the baud rate to",
)
@click.option(
    "-i",
    "--interface",
    required=True,
    type=click.Choice(
        choices=["VISA_SERIAL", "VISA_TCPIP", "SOCKET_TCPIP"], case_sensitive=False
    ),
    help="""The interface to use for the connection. Available interfaces are:
        - VISA_SERIAL - serial communication with pyvisa
        - VISA_TCPIP - TCP/IP communication with pyvisa's different protocols
        - SOCKET_TCPIP  - TCP/IP communication using socket""",
)
@click.option(
    "-ip",
    "--ip-address",
    required=False,
    help="The address of the device to connect to (needed with TCPIP interfaces).",
)
@click.option(
    "--name",
    required=False,
    type=click.Choice(REGISTERED_INSTRUMENTS, case_sensitive=False),
    default=None,
    help="""name of the instrument in use. If registered, the commands
        adapted to this instrument will be used instead of the default ones. """,
)
@click.option(
    "--log-level",
    required=False,
    default="INFO",
    type=click.Choice(
        "DEBUG INFO WARNING ERROR".split(" "),
        case_sensitive=False,
    ),
    help="set the verbosity of the logging",
)
@click.option(
    "--output-channel",
    required=False,
    type=click.STRING,
    default=None,
    help="""The index of the output channel instrument to use.
        Use 'get' to receive the currently used output channel.""",
)
@click.option(
    "-p",
    "--port",
    required=False,
    type=click.INT,
    default=None,
    help="""The port of the device to connect to. This is either a serial port for a VISA_SERIAL interface
        or an IP port in case of an TCPIP interfaces (required for VISA_SERIAL interface and SOCKET
        interface).""",
)
@click.option(
    "--protocol",
    required=False,
    default=None,
    type=click.Choice(
        "INSTR SOCKET HISLIP".split(" "),
        case_sensitive=True,
    ),
    help="""The protocol to use for the VISA_TCPIP interfaces. This usually is the last part of
    the complete instrument address, e.g. for 'TCPIP::1.1.1.1::HISLIP' this would be HISLIP.""",
)
# Interactive mode
@click.option(
    "--interactive",
    flag_value="interactive",
    required=False,
    default=None,
    help="Opens the interactive mode after a connection is established with the instrument",
)
# Use instrument method
@click.option(
    "--query",
    required=False,
    default=None,
    type=click.STRING,
    help="Send a query with a custom payload to the instrument",
)
@click.option(
    "--write",
    required=False,
    default=None,
    type=click.STRING,
    help="Send a write with a custom payload to the instrument",
)
# General
@click.option(
    "--identification",
    flag_value="get",
    required=False,
    default=None,
    help="Get the instrument's identification information",
)
@click.option(
    "--reset",
    flag_value="set",
    required=False,
    default=None,
    help="Reset the instrument",
)
@click.option(
    "--status-byte",
    flag_value="get",
    required=False,
    default=None,
    help="Get the instrument's status byte",
)
@click.option(
    "--all-errors",
    flag_value="get",
    required=False,
    default=None,
    help="Get all errors currently stored in the instrument",
)
@click.option(
    "--self-test",
    flag_value="get",
    required=False,
    default=None,
    help="Perform a self test of the instrument",
)
# Remote control
@click.option(
    "--remote-control",
    required=False,
    default=None,
    type=click.Choice("get on off".split(), case_sensitive=False),
    help="Instrument's remote control state",
)
# Output mode
@click.option(
    "--output-mode",
    required=False,
    default=None,
    type=click.Choice("get enable disable".split(), case_sensitive=False),
    help="Instrument's output mode",
)
# Nominal values
@click.option(
    "--voltage-nominal",
    flag_value="get",
    required=False,
    default=None,
    help="Instrument's nominal voltage (V)",
)
@click.option(
    "--current-nominal",
    flag_value="get",
    required=False,
    default=None,
    help="Instrument's nominal current (A)",
)
@click.option(
    "--power-nominal",
    flag_value="get",
    required=False,
    default=None,
    help="Instrument's nominal power (W)",
)
# Target values
@click.option(
    "--voltage-target",
    required=False,
    default=None,
    help="Instrument's target voltage (V)",
)
@click.option(
    "--current-target",
    required=False,
    default=None,
    help="Instrument's target current (A)",
)
@click.option(
    "--power-target",
    required=False,
    default=None,
    help="Instrument's target power (W)",
)
# Measurements
@click.option(
    "--voltage-measure",
    flag_value="get",
    required=False,
    default=None,
    help="Measure the instrument's voltage (so argument to be provided)",
)
@click.option(
    "--current-measure",
    flag_value="get",
    required=False,
    default=None,
    help="Measure the instrument's current (so argument to be provided)",
)
@click.option(
    "--power-measure",
    flag_value="get",
    required=False,
    default=None,
    help="Measure the instrument's power (so argument to be provided)",
)
# Limit values
@click.option(
    "--voltage-limit-low",
    required=False,
    default=None,
    help="Instrument's voltage lower limit",
)
@click.option(
    "--voltage-limit-high",
    required=False,
    default=None,
    help="Instrument's voltage higher limit",
)
@click.option(
    "--current-limit-low",
    required=False,
    default=None,
    help="Instrument's current lower limit",
)
@click.option(
    "--current-limit-high",
    required=False,
    default=None,
    help="Instrument's current higher limit",
)
@click.option(
    "--power-limit-high",
    required=False,
    default=None,
    help="Instrument's power higher limit",
)
@click.version_option(__version__)
def main(
    ip_address,
    baud_rate,
    interface,
    log_level,
    name,
    port,
    interactive,
    protocol,
    **kwargs,
) -> int:
    """
    Main function run by the CLI

    :param argv: The argument list passed via command line
    :return: None
    """
    # Initialize logging
    initialize_logging(log_level)

    # Setup and open the interface (SERIAL or TCPIP with VISA or TCPIP socket)
    instr_aux = setup_interface(
        interface=interface,
        baud_rate=baud_rate,
        ip_address=ip_address,
        port=port,
        name=name,
        protocol=protocol,
    )

    # Perform other commands from subparsers
    perform_actions(instr_aux=instr_aux, actions=kwargs)

    # Opens interactive mode
    if interactive:
        click.echo(
            "Interactive mode enabled. The connection to the instrument is still opened. "
            "Type other commands to get or set values, "
            "and then type 'exit' to exit the interactive session"
        )
        while 1:
            command = click.prompt("--")
            if command == "exit":
                click.echo("Exiting interactive session")
                break
            else:
                perform_actions(
                    instr_aux=instr_aux, actions=parse_user_command(command)
                )

    # Close the VISA interface and exit
    instr_aux.delete_instance()

    return ExitCode.SUCCESS.value


if __name__ == "__main__":
    sys.exit(main())
