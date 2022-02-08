### Changelog

All notable changes to this project will be documented in this file.

## Keywords
Commits are sorted into three categories based on keywords that can occur at any position as part of the commit message.
[Category] Keywords1, Keywords2
* [BREAKING CHANGES] BREAKING CHANGE
* [Features] feat:
* [Fixes] fix:
* [Docs] docs:
* [Styles] style:
* [Refactors] Refactors:
* [Performances] perf:
* [Tests] test:
* [Build] build:
* [Ci] ci:

* [Commits] (All commits that are not part of one of the other categories)
Each commit is considered only once according to the order of the categories listed above. Merge commits are ignored.

Generator command: `npm run change`
Commit helper: `cz c`


## [0.15.0](https://github.com/eclipse/kiso-testing/compare/0.0.0-alpha...0.15.0)


---
## 0.0.0-alpha
> 2022-01-20

#### Commits

- Initial code drop of pykiso [`924e3eb`](https://github.com/eclipse/kiso-testing/commit/924e3eb1e2468f09112bc03c3197785e09f6eb64)
- Add Jenkinsfile for python-tests [`a2007f8`](https://github.com/eclipse/kiso-testing/commit/a2007f81c4b738f18061ceeb6b6a99d2d6f82f24)
- Second contribution - one year later [`150eaf9`](https://github.com/eclipse/kiso-testing/commit/150eaf94be18bf563edc4628a56be774500ff028)
- - clean up the whole kiso-testing (except jenkins file) [`37050f7`](https://github.com/eclipse/kiso-testing/commit/37050f7117deb7926eb95e10098b8474107b90ee)
- - remove pytest related to python-can [`c74492a`](https://github.com/eclipse/kiso-testing/commit/c74492ad83f22d09d585e14b72f935bff12cc51b)
- - just erase useless config in pytest test_config_parser [`bbb7b41`](https://github.com/eclipse/kiso-testing/commit/bbb7b41c72591ed3a92c409d298ca3f30e996cd1)
- add read the doc yaml file [`cc32047`](https://github.com/eclipse/kiso-testing/commit/cc32047946501647693b3532638e6d14561cbc5a)
- - python version update  from readthedoc config file [`f614576`](https://github.com/eclipse/kiso-testing/commit/f6145762ad21b10f067cd2e728d1fa1964f58e83)
- add sphinx doc reauirement txt [`9de5361`](https://github.com/eclipse/kiso-testing/commit/9de53612a71f5bb12282ad46b8f95384c031a5f9)
- add logo to README.md [`63b3a57`](https://github.com/eclipse/kiso-testing/commit/63b3a57680cdd2fdacd1d1d54de4c33855d94a87)
- Add auxiliary and connector implementation tutorials [`a7eb94a`](https://github.com/eclipse/kiso-testing/commit/a7eb94acd1bc058e32d9793be86305fdf424374d)
- Update CCPcanCan tests [`6c8b1c9`](https://github.com/eclipse/kiso-testing/commit/6c8b1c95e97ffcaccefaa766921d57f59c2fbb60)
- prepare twine upload with jenkins [`a6fc89a`](https://github.com/eclipse/kiso-testing/commit/a6fc89a6b358fd742a1daa787aa10b9f2db4876d)
- Finish implementation examples [`fe9fc77`](https://github.com/eclipse/kiso-testing/commit/fe9fc772c2b214cbf780f0c7ae07172329515d39)
- Add library to API ref and finish cookbooks [`4a0c643`](https://github.com/eclipse/kiso-testing/commit/4a0c64306d52eb1bc8dd2b5bd2e33410876c315c)
- Add preface for auxiliary implementation tutorial [`5ff4350`](https://github.com/eclipse/kiso-testing/commit/5ff43502d643d16255867f27e0f964c095f426db)
- Split auxiliary execution paragraph [`47d4a93`](https://github.com/eclipse/kiso-testing/commit/47d4a93815af7369f229c70f4de41e41648af1d5)
- Rework auxiliary tutorial [`2dbb7fc`](https://github.com/eclipse/kiso-testing/commit/2dbb7fc69a280982ac0e1816fb79c5427346c79e)
- add upload stage to pypi [`cefdc33`](https://github.com/eclipse/kiso-testing/commit/cefdc3352ef864a05d6be716226fae60e6b901dd)

---

<!-- auto-changelog-above -->

### Version 0.14.0

Features:
- add test name on failure (print: test name, description and reason)
- manage RTT connector resource consumption using rtt_log_speed parameter
- repeat testCases upon failure (x run, 1 successful -> ok & go)
- repeat testCases for stability test (x run, 1 failure -> not ok & go)
- add reset function and decorator to RTT connector
- add functionalities to recorder auxiliary

Changes:
- move error messages from python-can 4.0.0 into log level debug
- add timeout in the receive method in order to to send the signal to the GIL to change thread
- add Repeat test upon failure examples and documentation

Bugfix:
- Empty multiprocessing queue in instance deletion to avoid auxiliary hanging issues(workaround)

### Version 0.13.1 (internal release)

Bugfix:
- correct junit reporting instability by flushing StreamHandler at each test cases start

Features:
- *BREAKING CHANGE*: Improve test fixture labeling by introducing branch_level params

### Version 0.13.0 (internal release)

Changes:
- set message reception size to buffer size in CCRttSegger if raw is set
- Change pykiso import order for new vsc intellisense approach

Bugfix:
- fix wrong exit code return when an exception is raised at suite collection level

Features:
- add BannerTestResult to show test execution results in a banner

### Version 0.12.1 (internal release)

Bugfix:
- Variant skipped but case_setup and case_teardown kept executed

Features:
- add capability to read target memory to jlink connector

### Version 0.12.0 (internal release)

Features:
- add PATTERN argument in CLI to overwrite the test_filter_pattern


### Version 0.11.1 (internal release)

Changes:
- remove brainstem libs because of installations conflicts

### Version 0.11.0 (internal release)

Changes:
- Add external brainstem package for local installation

Features:
- add record auxiliary
- add acroname robot auxiliary
- add auxiliary to control acroname usb hubs
- add multiprocessing based auxiliary interface
- add multiprocessing proxy auxiliary version
- add multiprocessing proxy channel version
- add simple auxiliary interface

Changes:
- put thread and multiprocessing based auxiliary interface in a dedicated folder
- make acroname auxiliary inherit from SimpleAuxiliaryInterface
- make instrument auxiliary inherit from SimpleAuxiliaryInterface

### Version 0.10.3 (internal release)

Changes:
- Move back to threading RLock instead of multiprocessing one for CChannel interface

### Version 0.10.2 (internal release)

Features:
- add variant option to pykiso command
- add package requirements into the yaml file (version check)

Bugfix:
- improve proxy auxiliary stability
- fix sporadic issue seen when CTRL+C is pressed(UnboundLocalError)


### Version 0.10.1 (internal release)

Features:
- add reset in CCRttSegger if the debugger is halted

Bugfix:
- explicitly cast fdx connector and flasher params
- set CCRttSegger serial_no to None if the given one is not an int
- fix flash-lauterbach to wait properly till scripts are executed.


### Version 0.10.0

Features:
- add capability to generate a trace file for proxy auxiliary
- add PCAN connector
- add Vector-CAN connector
- Run proxy aux on a different process to improve cpu utilization.
  E.g. cycle time of network status message has less jitter.

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
- fix connection issues when t32 executable is not able to start

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
- added automatic detection of Vector Boxes' serial number
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

Features:

Changes:

Bugfixes:
- fixed bug when generating junit report and reports folder does not exist
- fixed bug Vector serial number with leading zeros


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
- add PCAN connector
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
