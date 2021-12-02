### Current Version

Features:
- add capability to generate a trace file for proxy auxiliary
- add PCAN connector
- add Vector-CAN connector

Bugfix:
- failing attempt to quit trace32 will not affect the pykiso test result
- resolve folder naming conflicts when parsing the config file
- flash-jlink didn't connect to given serial number

### Version 0.9.4 (internal release)

Features:
- introduce is_pausable flag to force an auxiliary to wait
- add logger activation for all auxiliaries

Changes:
- make instrument control auxiliary respect auxiliary interface
- deactivate all non-pykiso loggers

Bugfix:
- log any error when loading multiple testsuites

### Version 0.9.3 (internal release)

Features:
- add environment variable casting for float, bool, etc.

Changes:
- refactor parse_config and move it in config_parser.py

Bugfix:
- fix connection issues when t32 is already running
- fix connection issues when t32mppc is not able to start

### Version 0.9.2 (internal release)

Features:
- add environment variable casting for integer-like strings
- warn user and raise NotImplementedError when an auxiliary is not proxy compatible
- add templates for all available features, auxiliaries and connectors

Bugfix:
- correct issue on InstrumentControlAuxiliary using 'Rohde&Schwarz' instrument name
- correct error when opening cc_tcp_ip with the wrong IP address

### Version 0.9.1 (internal release)

Bugfix:
- fix log capability

### Version 0.9.0 (internal release)

Features:
- add tcp/ip socket connector
- add SOCKET interface to instrument_control_cli
- add stdout writing in junit report
- add line number in logging message format

Bugfix:
- correct issue on proxy connector/auxiliary deletion phase
- correct issue on proxy auxiliary regarding late auxiliary import magic
- correct performance issues when auxiliaries are suspended
- correct validation mechanism in InstrumentControlAuxiliary

### Version 0.8.1 (internal release)

Features:
- add robot framework version of proxy auxiliary
- add robot framework version of instrument control auxiliary
- add RTT log reading in cc_rtt_segger

Changes:
- adapt robot communication auxiliary keywords

Bugfix:
- remove all sphinx documentation generation warnings

### Version 0.8.0 (internal release)

Features:
- DUTAuxiliary can be used with the robotframework to control the TestApp
- add new VISA connectors in cc_visa for VISA communication via serial and TCP/IP
- add new instrument_control_auxiliary that uses the VISA connectors to communicate with instruments.
- add two examples and a command line interface to control the instrument.
- the test reference (eg: JAMA) can be assigned

Changes:
- improve code for robot package
- Update AuxiliaryInterface run method in order to avoid None value in queue_out.

Bugfix:
- adapt return values from receive_message method for robot communication auxiliary

Tests:
- add unit tests for framework package (interface, loader and communication aux)

### Version 0.7.0 (internal release)

Features:
- add auxiliary resume and suspend capabilities

### Version 0.6.1 (internal release)

Bugfix:
- fix issue in config parser when entity name matches folder name

### Version 0.6.0 (internal release)

Features:
- modify define_test_parameters decorator in order to have parametrized timeout for each test fixtures.
- add reset functionality for the cc_fdx_lauterbach

Changes:
- adapt ExampleAuxiliary timeout value

Bugfix
- fix test case run scenario for DUT simulation
- fix import issue for test_suite_virtual (UDP server has to be first)

Tests:
-add pytest regarding define_test_parameters decorator modification

### Version 0.5.1 (internal release)

Changes:
- track python guidelines
- split file test_factory_and_execution.py into test_execution and config_registry
- restructured files into folders test_coordinator and test_setup

Bugfix
- fix parsing of environment variables in the connectors config

### Version 0.5.0 (internal release)

Features:
- add proxy connector
- add proxy auxiliary
- allow relative paths in yaml file
- add nested yaml capability (introduce !include tag)

Changes:
- add docstrings and typehints for several connector implementation
- remove usage of timeout parameter for cc_send method in CChannel class
- add parameter kwargs for cc_send method in CChannel class

Tests:
- add pytest for proxy connector
- add pytest for proxy auxiliary
- adapt test_simulated_auxiliary (use of sys.exit)
- set pytest logging level to INFO
- add test for cli.py

### Version 0.4.0 (internal release)

Bugfixes:
- fixed bug when generating junit report and reports folder does not exist

### Version 0.3.0 (internal release)

Changes:
- adding module-specific log in pykiso

Bugfixes:
- fixed bug enum34 package during developers installation

Tests:
- adapt tests which uses log to use module-specific logs
- correct tests for test_factory_and_execution module

### Version 0.2.0 (internal release)

Features:
- add cli option for junit report generation
- add automated jenkins run of the dummy.yaml file
- add reports folder in which the junit reports are saved
- add the ability to use environment variables in YAML files

Changes:
- modify define_test_parameters decorator to get the test case infos in the test results and test reports.
- Implement the catch of KeyboardInterrupt exception during pykiso execution

Bugfixes:
- fixed a bug in the flash_Lauterbach connector
- fixed reading of the messages from TestApp on pykiso side

Tests :
- add tests for test_factory_and_execution with different reporting options.

### Version 0.1.0 (internal release)

Features:
- add Device Under Test Auxiliary (DUT)
- add Segger RTT connector (communication channel)
- add dummy jenkins file

Changes:
- add example/configuration file for Segger RTT channel (flasher and communication)
- update sphinx documentation

Bugfixes:
- fix message segmentation issue on reception for Segger RTT connector
- fix management of LOG message type from test protocol
- fix flash procedure for Segger RTT connector (flasher channel)
- fix typo issues

Tests :
- add unit tests for DUT auxiliary
- add unit tests for Segger RTT connector
- adapt integration tests (using virtual auxiliary) for DUT auxiliary


### Version 0.0.0

Initial version
