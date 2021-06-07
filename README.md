# Integration Test Framework

Python based integration test automation framework.

## Requirements

* Python 3.6+
* pip/pipenv (used to get the rest of the requirements)

## Install for ITF users (I want to write tests with the ITF)

* For **CONAN** installation(available for windows), please check https://dev-bosch.com/confluence/x/gsAxBQ
* For manual installation, please follow the readme.md here: https://dev-bosch.com/bitbucket/projects/PEA/repos/integration-test-framework-eco-system/browse/README.md

## Install for ITF developers (I want to develop, extend bugfix, improve the ITF)

[Pipenv](https://github.com/pypa/pipenv) is more appropriate for developers as it automatically creates virtual environments.

```bash
git clone <repo address>
cd integration-test-framework
pipenv install --dev
pipenv shell
```

### Pre-Commit

To improve code-quality, a configuration of [pre-commit](https://pre-commit.com/) hooks are available.
The following pre-commit hooks are used:

- black
- trailing-whitespace
- end-of-file-fixer
- check-docstring-first
- check-json
- check-added-large-files
- check-yaml
- debug-statements

If you don't have pre-commit installed, you can get it using pip:

```bash
pip install pre-commit
```

Start using the hooks with

```bash
pre-commit install
```
## Pykiso Usage

Once installed the application is bound to `pykiso`, it can be called with the following arguments:

```bash
Usage: pykiso [OPTIONS]

  Embedded Integration Test Framework

Options:
  -c, --test-configuration-file FILE
                                  path to the test configuration file (in YAML
                                  format)  [required]

  -l, --log-path PATH             path to log-file or folder. If not set will
                                  log to STDOUT

  --log-level [DEBUG|INFO|WARNING|ERROR]
                                  set the verbosity of the logging
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

Suitable config files are available in the `test-examples` folder.

### Demo using example config

```bash
invoke run
```

### Running the Tests

```bash
invoke test
```

or

```bash
pytest
```

## Instrument Control Usage

Once installed, the `instrument-control` command is available. It can be called with the following arguments:

### Basic Usage

```bash
Usage: instrument-control [OPTIONS]

  Main function run by the CLI

  :param argv: The argument list passed via command line :return: None

Options:
  -b, --baud-rate INTEGER         The value to set the baud rate to
  -i, --interface [VISA_SERIAL|VISA_TCPIP|SOCKET_TCPIP]
                                  The interface to use for the connection.
                                  Available interfaces are: - VISA_SERIAL -
                                  serial communication with pyvisa -
                                  VISA_TCPIP - TCP/IP communication with
                                  pyvisa's different protocols - SOCKET_TCPIP
                                  - TCP/IP communication using socket
                                  [required]

  -ip, --ip-address TEXT          The address of the device to connect to
                                  (needed with TCPIP interfaces).

  --name [Elektro-Automatik|Rohde&Schwarz]
                                  name of the instrument in use. If
                                  registered, the commands adapted to this
                                  instrument will be used instead of the
                                  default ones.

  --log-level [DEBUG|INFO|WARNING|ERROR]
                                  set the verbosity of the logging
  --output-channel TEXT           The index of the output channel instrument
                                  to use. Use 'get' to receive the currently
                                  used output channel.

  -p, --port INTEGER              The port of the device to connect to. This
                                  is either a serial port for a VISA_SERIAL
                                  interface or an IP port in case of an TCPIP
                                  interfaces (required for VISA_SERIAL
                                  interface and SOCKET interface).

  --protocol [INSTR|SOCKET|HISLIP]
                                  The protocol to use for the VISA_TCPIP
                                  interfaces. This usually is the last part of
                                  the complete instrument address, e.g. for
                                  'TCPIP::1.1.1.1::HISLIP' this would be
                                  HISLIP.

  --interactive                   Opens the interactive mode after a
                                  connection is established with the
                                  instrument

  --query TEXT                    Send a query with a custom payload to the
                                  instrument

  --write TEXT                    Send a write with a custom payload to the
                                  instrument

  --identification                Get the instrument's identification
                                  information

  --reset                         Reset the instrument
  --status-byte                   Get the instrument's status byte
  --all-errors                    Get all errors currently stored in the
                                  instrument

  --self-test                     Perform a self test of the instrument
  --remote-control [get|on|off]   Instrument's remote control state
  --output-mode [get|enable|disable]
                                  Instrument's output mode
  --voltage-nominal               Instrument's nominal voltage (V)
  --current-nominal               Instrument's nominal current (A)
  --power-nominal                 Instrument's nominal power (W)
  --voltage-target TEXT           Instrument's target voltage (V)
  --current-target TEXT           Instrument's target current (A)
  --power-target TEXT             Instrument's target power (W)
  --voltage-measure               Measure the instrument's voltage (so
                                  argument to be provided)

  --current-measure               Measure the instrument's current (so
                                  argument to be provided)

  --power-measure                 Measure the instrument's power (so argument
                                  to be provided)

  --voltage-limit-low TEXT        Instrument's voltage lower limit
  --voltage-limit-high TEXT       Instrument's voltage higher limit
  --current-limit-low TEXT        Instrument's current lower limit
  --current-limit-high TEXT       Instrument's current higher limit
  --power-limit-high TEXT         Instrument's power higher limit
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

### Demos using example instrument

For all following examples, assume that we are connecting to a serial instrument on port COM4.

Requesting basic information from the instrument:

```bash
    instrument-control -i VISA_SERIAL -p 4 --identification
```

Request basic information from the instrument via the SOCKET_TCPIP interface:

```bash
    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --identification
```

Reset the device with VISA_TCPIP interface and the address 10.10.10.10:

```bash
    instrument-control -i VISA_TCPIP -ip 10.10.10.10 --reset
```

Also reset the instrument, but use the VISA_SERIAL on port 4 and set the baud rate to 9600:

```bash
    instrument-control -i VISA_SERIAL -p 4 --baud-rate 9600 --reset
```

Get the currently selected output channel from a Rohde & Schwarz device

```bash
    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --name "Rohde&Schwarz" --output-channel get
```

Set the output channel from a Rohde & Schwarz device to channel 3

```bash
    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --name "Rohde&Schwarz" --output-channel 3
```

Read the target value for the current

```bash
    instrument-control -i VISA_SERIAL -p 4 --current-target
```

Set the current target to 1.0 Ampere

```bash
    instrument-control -i VISA_SERIAL -p 4 --current-target 1.0
```

Enable remote control on the instrument

```bash
    instrument-control -i VISA_SERIAL -p 4 --remote-control ON
```

Set the voltage to 35 Volts and then enable the output:

```bash
    instrument-control -i VISA_SERIAL -p 4 --voltage-target 35.0 --output-mode ENABLE
```

Get the instrument's identification information by sending custom a query command:

```bash
    instrument-control -i VISA_SERIAL -p 4 --query *IDN?
```

Reset the instrument by sending a custom write command:

```bash
    instrument-control -i VISA_SERIAL -p 4 --write *RST
```

Example interacting with a remote instrument:

Measuring the current voltage on channel 3:

```bash
    instrument-control -i SOCKET_TCPIP -ip 10.10.10.10 -p 5025 --output-channel 3 --voltage-measure
```

### Interactive mode

The CLI includes an interactive mode. You can use it by adding the `--interactive` flag
when you call the instrument-control CLI. Once you are inside this interactive mode,
you can send commands one after the other. You may use all the available commands (you can remove the double dash).

Example:

1. Enter interactive mode,
1. get the identification information,
1. query the currently selected output channel,
1. set the output-channel to 3,
1. apply 36V,
1. then measure the voltage.

```bash
    instrument-control -i VISA_SERIAL -p 4 --identification get --interactive
    output-channel
    output-channel 3
    remote-control on
    voltage-target 36
    output-mode enable
    voltage-measure
    exit
```

## List of limitations / todos for the python side

* [ ] **When the auxiliary does not answer (ping or else), GenericTest.BasicTest.cleanup_and_skip() call will result in a lock and break the framework.**
* [ ] No test-setion will be executed, needs to be removed later.
* [x] test configuration files need to be reworked
* [x] Names & configurations in the *cfg file json* are character precise class names & associated parameters.
* [ ] Spelling mistakes need to be fixed!  _*ongoing*_
* [ ] Add verbosity parameters to pass to the unittest framework to get more details about the test.
* [ ] **Add result parsing for Jenkins (see: https://stackoverflow.com/questions/11241781/python-unittests-in-jenkins).**
* [x] Create a python package
    * [ ] and host it on pip.
