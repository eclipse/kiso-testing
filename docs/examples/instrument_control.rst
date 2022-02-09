.. _instrument_control_aux:

Controlling an Instrument
=========================

The instrument-control command offers a way to interface with an arbitrary instrument, such as power supplies from different brands.
The Standard Commands for Programmable Instruments (SCPI) protocol is used to control the desired instrument.
This section aims to describe how to use instrument-control as an auxiliary for integration testing, and also how to interface directly
with the instrument using the built-in command line interface (CLI).


Requirements
------------

A successful pykiso installation as described in this chapter: :ref:`pykiso_installation`


Integration Test Usage
----------------------

The auxiliary functionalities can be used during integration tests.

Add Test file:
See the dedicated section below: :ref:`instrument_control_integration_test`

Add Config File
In your test configuration file, provide what is necessary to interface with the instrument:

- Chose between the VISASerial and the VISATcpip connector
- If you are using a serial interface, the `serial_port` must be provided in the connector configuration, and the `baud_rate` is optional.
- If you are using a tcpip interface, the `ip_address` must be provided in the connector configuration.
- Chose the InstrumentControlAuxiliary

.. note:: You cannot use the instrument-control auxiliary with a proxy.

- The SCPI commands might be different or even not available depending on the instrument that you are using. If you provide an `instrument`
    parameter and the instrument is recognized, the functions in the `lib_scpi` will automatically be adapted according to your instrument capabilities and specificities.
- If your instrument has more than one output channel, provide the one to use in `output_channel`.

Example of a test configuration file using instrument-control auxiliary:

Examples:

.. literalinclude:: ../../examples/power_supply_control_EA_PSI9000.yaml
    :language: yaml
    :linenos:

.. literalinclude:: ../../examples/power_supply_control_RS_remote.yaml
    :language: yaml
    :linenos:

.. _instrument_control_integration_test:

Implementation of Instrument Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the instrument auxiliary (`instr_aux`) inside integration tests is useful to control the instrument (e.g. a power supply) the device under test is connected to. There are two different ways to interface with an instrument:

#. The first option is to use the `read`, `write`, and `query` commands to directly send SCPI commands to the instrument. If you use this method, refer to your instrument's datasheet to get the appropriate SCPI commands.
#. The other option is to use the built-in functionalities from the library to communicate with the instrument. For that, use the `lib_scpi` attribute of your `instru_aux` auxiliary.

You can then send `read`, `write` and `query` (`write` + `read`) requests to the instrument.

For example:
#. To query the identification data of your instrument, you can use `instr_aux.query("*IDN?")`
#. To set the voltage target value to 12V, you can use `instr_aux.write("SOUR:VOLT 12.0")`

Some helper commands have already been implemented to simplify the testing. For example, using helpers:
#. To query the identification data of your instrument: `instr_aux.helpers.get_identification()`.
#. To set the voltage target value to 12V: `instr_aux.helpers.set_target_voltage(12.0)`

Notice that the SCPI command can be different depending on the instrument. For some instrument, some features are also unavailable. Please refer to your instrument's datasheet for details.
    Some instruments are already registered. If you specify the name of the instrument that you are using in the YAML file, the helpers function will select and use the SCPI commands that are appropriate or tell you if the command is not available.

When setting a parameter on the instrument, it is possible to use a validation procedure to make sure that the parameter was successfully changed to the desired value.
    The validation procedure consists in sending a query immediately after sending the write command, the answer of the query will then tell if the write command was successful or not.
    For instance, in order to enable the output on the currently selected channel of the instrument, we can use `instr_aux.write("OUTP ON")`, or, using the validation procedure, `instr_aux.write("OUTP ON", ("OUTP?", "ON"))`.
    Notice that the validation parameter is a tuple of the form ('query to send to check the writing operation', 'expected answer')
    When the expected answer is a number, please use the "VALUE{}" tag. For instance, you can use `instr_aux.write("SOUR:VOLT 12.5", ("SOUR:VOLT?", "VALUE{12.5}"))`. That way, it does not matter if the instrument returns `12.50`, `12.500` or `1.25000E1`,
    the writing operation will be considered successful.
    Also, if you are not sure what your instrument will respond to the validation, you can compare that output to a list of string, instead on a single string. For example, you can use `instr_aux.write("OUTP ON", ("OUTP?", ["ON", "1"]))`. The `VALUE` should not passed inside a list.
    This validation procedure is used in all the helper functions (except reset)

The following integration test file will provide some examples:

**instrument_test.py**:

.. code:: python

    import logging
    import time

    import pykiso
    from pykiso.auxiliaries import instr_aux


    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[instr_aux])
    class TestWithPowerSupply(pykiso.BasicTest):
        def setUp(self):
            """Hook method from unittest in order to execute code before test case run."""
            logging.info(
                f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
            )

        def test_run(self):
            logging.info(
                f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
            )

            logging.info("---General information about the instrument:")
            # using the auxiliary's 'query' method
            logging.info(f"Info: {instr_aux.query('*IDN?')}")
            # using the commands from the library
            logging.info(f"Status byte: {instr_aux.helpers.get_status_byte()}")
            logging.info(f"Errors: {instr_aux.helpers.get_all_errors()}")
            logging.info(f"Perform a self-test: {instr_aux.helpers.self_test()}")

            # Remote Control
            logging.info("Remote control")
            instr_aux.helpers.set_remote_control_off()
            instr_aux.helpers.set_remote_control_on()

            # Nominal values
            logging.info("---Nominal values:")
            logging.info(f"Nominal voltage: {instr_aux.helpers.get_nominal_voltage()}")
            logging.info(f"Nominal current: {instr_aux.helpers.get_nominal_current()}")
            logging.info(f"Nominal power: {instr_aux.helpers.get_nominal_power()}")

            # Current values
            logging.info("---Measuring current values:")
            logging.info(f"Measured voltage: {instr_aux.helpers.measure_voltage()}")
            logging.info(f"Measured current: {instr_aux.helpers.measure_current()}")
            logging.info(f"Measured power: {instr_aux.helpers.measure_power()}")

            # Limit values
            logging.info("---Limit values:")
            logging.info(f"Voltage limit low: {instr_aux.helpers.get_voltage_limit_low()}")
            logging.info(
                f"Voltage limit high: {instr_aux.helpers.get_voltage_limit_high()}"
            )
            logging.info(f"Current limit low: {instr_aux.helpers.get_current_limit_low()}")
            logging.info(
                f"Current limit high: {instr_aux.helpers.get_current_limit_high()}"
            )
            logging.info(f"Power limit high: {instr_aux.helpers.get_power_limit_high()}")

            # Test scenario
            logging.info("Scenario: apply 36V on the selected channel for 1s")
            dc_voltage = 36.0  # V
            dc_current = 1.0  # A
            logging.info(
                f"Set voltage to {dc_voltage}V: {instr_aux.helpers.set_target_voltage(dc_voltage)}"
            )
            logging.info(
                f"Set voltage to {dc_current}V: {instr_aux.helpers.set_target_current(dc_current)}"
            )
            logging.info(f"Switch on output: {instr_aux.helpers.enable_output()}")
            logging.info("sleeping for 1s")
            time.sleep(0.5)
            logging.info(f"measured voltage: {instr_aux.helpers.measure_voltage()}")
            logging.info(f"measured current: {instr_aux.helpers.measure_current()}")
            time.sleep(0.5)
            logging.info(f"Switch off output: {instr_aux.helpers.disable_output()}")

            logging.info(
                f"Trying to set an impossible value (1000V) {instr_aux.helpers.set_target_voltage(1000)}"
            )

        def tearDown(self):
            """Hook method from unittest in order to execute code after test case run."""
            logging.info(
                f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
            )

Command Line Usage
------------------

The auxiliary functionalities can also be used from a command line interface (CLI).
This section provides a basic overview of exemplary use cases processed through the CLI, as well as a general overview
of all possible commands.


Connection to the instrument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every tine that the instrument-control CLI will be called, a connection to the instrument will be opened. Then, some actions and/or measurement will be
done, and the connection will finally be closed.
As a consequence, you should always give the necessary options to be able to connect to the instrument.

- Chose an interface (`VISA_SERIAL`, `VISA_TCPIP`, or `SOCKET_TCPIP`). Use `-i` or `--interface`. This option is mandatory.
- Use the `-p`/`--port`, the `-ip`/`--ip-address`. Several option are available for the different interfaces:
    - VISA_TCPIP: you must provide an ip address, the port is optional.
    - VISA_SERIAL: you must indicate the serial port to use.
    - SOCKET_TCPIP: you must have to set the ip address and a port.
- You can add a `-b`/`--baud-rate` option if you chose a SERIAL interface
- You can add a `--name` option to indicate that you are using a specific instrument. If this instrument is registered, the SCPI command specific to this instrument will be used instead of the default commands. For instance, selecting the output channel is not possible for Elektro-Automatik instruments because they only have one. The Rhode & Schwarz on the other hand does, so the corresponding commands are available.
- You can add a `--log-level` option to indicate the logging verbosity.

Performing measurement and setting values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can then use other options to perform measurements and set values on your instrument.
For that use the following options.

Flag options:

- Get the instrument identification information: `--identification`
- Resets the instrument: `--reset`
- Get the instrument status byte: `--status-byte`
- Get the errors currently stored in the instrument: `--all-errors`
- Performs a self test of the instrument: `--self-test`

- Get the instrument voltage nominal value: `--voltage-nominal`
- Get the instrument current nominal value: `--current-nominal`
- Get the instrument power nominal value: `--power-nominal`

- Measures voltage on the instrument: `--voltage-measure`
- Measures current on the instrument: `--current-measure`
- Measures power on the instrument: `--power-measure`

Options with values (specify a floating value for the parameter that you want to set on the instrument.
If you want to get the value currently set on the instrument, write `get` instead of the numeric value)

- Instrument's output channel: `--output-channel`

- Instrument's voltage target value: `--voltage-target`
- Instrument's current target value: `--current-target`
- Instrument's power target value: `--power-target`

- Instrument's voltage lower limit: `--voltage-limit-low`
- Instrument's voltage higher limit: `--voltage-limit-high`
- Instrument's current lower limit: `--current-limit-low`
- Instrument's current higher limit: `--current-limit-high`
- Instrument's power higher limit: `--power-limit-high`

Other options with values:

- Instrument's remote control: `--remote-control`. Use `get` to get the remote control state, `on` to enable and `off` to disable the remote control on the instrument. - Instrument's output mode (output channel enable/disabled): `--output-mode`. Use `get` to get the remote control state, `enable` to enable and `disable` to disable the output of the currently selected channel of the instrument.

You can also send custom write and query commands:

- Send custom query command: `--query`
- Send custom write command: `--write`

Usage Examples
~~~~~~~~~~~~~~

For all following examples, assume that we are connecting to a serial instrument on port COM4.

Requesting basic information from the instrument:

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --identification

Request basic information from the instrument via the SOCKET_TCPIP interface:

.. code:: bash

    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --identification

Reset the device with VISA_TCPIP interface and the address 10.10.10.10:

.. code:: bash

    instrument-control -i VISA_TCPIP -ip 10.10.10.10 --reset

Also reset the instrument, but use the VISA_SERIAL on port 4 and set the baud rate to 9600:

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --baud-rate 9600 --reset

Get the currently selected output channel from a Rohde & Schwarz device

.. code:: bash

    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --name "Rohde&Schwarz" --output-channel get

Set the output channel from a Rohde & Schwarz device to channel 3

.. code:: bash

    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --name "Rohde&Schwarz" --output-channel 3

Read the target value for the current

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --current-target

Set the current target to 1.0 Ampere

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --current-target 1.0

Enable remote control on the instrument

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --remote-control ON

Set the voltage to 35 Volts and then enable the output:

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --voltage-target 35.0 --output-mode ENABLE

Get the instrument's identification information by sending custom a query command:

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --query *IDN?

Reset the instrument by sending a custom write command:

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --write *RST

Example interacting with a remote instrument:

Measuring the current voltage on channel 3:

.. code:: bash

    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --output-channel 3 --voltage-measure

Interactive mode
~~~~~~~~~~~~~~~~
The CLI includes an interactive mode. You can use it by adding the `--interactive` flag
when you call the instrument-control CLI. Once you are inside this interactive mode,
you can send commands one after the other. You may use all the available commands (you can remove the double dash).

Example:

#. Enter interactive mode,
#. get the identification information,
#. query the currently selected output channel,
#. set the output-channel to 3,
#. apply 36V,
#. and then measure the voltage.

.. code:: bash

    instrument-control -i VISA_SERIAL -p 4 --identification get --interactive
    output-channel
    output-channel 3
    remote-control on
    voltage-target 36
    output-mode enable
    voltage-measure
    exit


General Command Overview
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    instrument-control --help
