
Robot Framework
===============

Integration Test Framework auxiliary<->connector mechanism is usable with Robot framework.
In order to achieve it, extra plugins have been developed :

- RobotLoader : handle the import magic mechanism
- RobotComAux : keyword declaration for existing CommunicationAuxiliary

.. note:: See `Robot framework <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html>`__
	regarding details about Robot keywords, cli...

How to
------

To bind ITF with Robot framework, the RobotLoader library has to be used in order to correctly create
all auxiliaries and connectors (using the "usual" yaml configuration style). This step is mandatory, and
could be done using the "Library" keyword and RobotLoader install/uninstall function. For example, inside
a test suite using "Suite Setup" and "Suite Teardown":

.. code-block:: robotframework

   *** Settings ***
   Documentation   How to handle auxiliaries and connectors creation using Robot framework

   Library    pykiso.lib.robot_framework.loader.RobotLoader    robot_com_aux.yaml    WITH NAME    Loader

   Suite Setup       Loader.install
   Suite Teardown    Loader.uninstall


Ready to Use Auxiliaries
------------------------

Communication Auxiliary
~~~~~~~~~~~~~~~~~~~~~~~

This plugin only contains two keywords "Send message" and "Receive message". The first one simply
sends raw bytes using the associated connector and the second one returns one received message (raw form).

See below a complete example of the Robot Communication Auxiliary plugin:

.. code-block:: robotframework

  *** Settings ***
  Documentation   Robot framework Demo for communication auxiliary implementation

  Library    pykiso.lib.robot_framework.communication_auxiliary.CommunicationAuxiliary    WITH NAME    ComAux

  *** Keywords ***

  send raw message
      [Arguments]  ${raw_msg}  ${aux}
      ${is_executed}=    ComAux.Send message    ${raw_msg}    ${aux}
      [return]  ${is_executed}

  get raw message
      [Arguments]  ${aux}  ${blocking}  ${timeout}
      ${msg}  ${source}=    ComAux.Receive message    ${aux}    ${blocking}    ${timeout}
      [return]  ${msg}  ${source}

  *** Test Cases ***

  Test send raw bytes using keywords
      [Documentation]    Simply send raw bytes over configured channel
      ...                using defined keywords

      ${state}  send raw message    \x01\x02\x03    aux1

      Log    ${state}

      Should Be Equal   ${state}    ${TRUE}

      ${msg}  ${source}  get raw message    aux1    ${TRUE}    0.5

      Log    ${msg}

  Test send raw bytes
      [Documentation]    Simply send raw bytes over configured channel
      ...                using communication auxiliary methods directly

      ${state} =  Send message    \x04\x05\x06    aux2

      Log    ${state}

      Should Be Equal   ${state}    ${TRUE}

      ${msg}  ${source} =  Receive message    aux2    ${FALSE}    0.5

      Log    ${msg}

Dut Auxiliary
~~~~~~~~~~~~~

This plugin can be used to control the ITF TestApp on the DUT.


See below an example of the Robot Dut Auxiliary plugin:

.. code-block:: robotframework

   *** Settings ***
   Documentation   Test demo with RobotFramework and ITF TestApp

   Library    pykiso.lib.robot_framework.dut_auxiliary.DUTAuxiliary    WITH NAME    DutAux

   Suite Setup       Setup Aux

   *** Keywords ***
   Setup Aux
       @{auxiliaries} =    Create List  aux1  aux2
       Set Suite Variable  @{suite_auxiliaries}  @{auxiliaries}

   *** Variables ***

   *** Test Cases ***

   Test TEST_SUITE_SETUP
       [Documentation]   Setup test suite on DUT
       Test App    TEST_SUITE_SETUP  1  1  ${suite_auxiliaries}

   Test TEST_SECTION_RUN
       [Documentation]   Run test section on DUT
       Test App    TEST_SECTION_RUN  1  1  ${suite_auxiliaries}

   Test TEST_CASE_SETUP
       [Documentation]   Setup test case on DUT
       Test App    TEST_CASE_SETUP  1  1  ${suite_auxiliaries}

   Test TEST_CASE_RUN
       [Documentation]   Run test case on DUT
       Test App    TEST_CASE_RUN  1  1  ${suite_auxiliaries}

   Test TEST_CASE_TEARDOWN
       [Documentation]   Teardown test case on DUT
       Test App    TEST_CASE_TEARDOWN  1  1  ${suite_auxiliaries}

   Test TEST_SUITE_TEARDOWN
       [Documentation]   Teardown test suite on DUT
       Test App    TEST_SUITE_TEARDOWN  1  1  ${suite_auxiliaries}

Proxy Auxiliary
~~~~~~~~~~~~~~~

This robot plugin only contains two keywords : Suspend and Resume.

See below example :

.. code-block:: robotframework

   *** Settings ***
   Documentation   Robot framework Demo for proxy auxiliary implementation

   Library    pykiso.lib.robot_framework.proxy_auxiliary.ProxyAuxiliary    WITH NAME    ProxyAux


   *** Test Cases ***

   Stop auxiliary run
       [Documentation]    Simply stop the current running auxiliary

       Suspend    ProxyAux

   Resume auxiliary run
       [Documentation]    Simply resume the current running auxiliary

       Resume    ProxyAux


Instrument Control Auxiliary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the "ITF" instrument control auxiliary, the robot version integrate exactly
the same user's interface.

.. note:: All return types between "ITF" and "Robot" auxiliary's version stay
  identical!

Please find below a complete correlation table:

+--------------------------+--------------------------+--------------+-------------+-------------+
| ITF method               | robot equivalent         | Parameter 1  | Parameter 2 | Parameter 3 |
+==========================+==========================+==============+=============+=============+
| write                    | Write                    | command      | aux alias   | validation  |
+--------------------------+--------------------------+--------------+-------------+-------------+
| read                     | Read                     | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| query                    | Query                    | command      | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_identification       | Get identification       | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_status_byte          | Get status byte          | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_all_errors           | Get all errors           | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| reset                    | Reset                    | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| self_test                | Self test                | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_remote_control_state | Get remote control state | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_remote_control_on    | Set remote control on    | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_remote_control_off   | Set remote control off   | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_output_channel       | Get output channel       | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_output_channel       | Set output channel       | channel      | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_output_state         | Get output state         | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| enable_output            | Enable output            | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| disable_output           | Disable output           | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_nominal_voltage      | Get nominal voltage      | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_nominal_current      | Get nominal current      | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_nominal_power        | Get nominal power        | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| measure_voltage          | Measure voltage          | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| measure_current          | Measure current          | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| measure_power            | Measure power            | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_target_voltage       | Get target voltage       | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_target_current       | Get target current       | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_target_power         | Get target power         | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_target_voltage       | Set target voltage       |voltage       | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_target_current       | Set target current       |current       | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_target_power         | Set target power         |power         | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_voltage_limit_low    | Get voltage limit low    | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_voltage_limit_high   | Get voltage limit high   | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_current_limit_low    | Get current limit low    | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_current_limit_high   | Get current limit high   | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| get_power_limit_high     | Get power limit high     | aux alias    |             |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_voltage_limit_low    | Set voltage limit low    | voltage limit| aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_voltage_limit_high   | Set voltage limit high   | voltage limit| aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_current_limit_low    | Set current limit low    | current limit| aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_current_limit_high   | Set current limit high   | current limit| aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+
| set_power_limit_high     | Set power limit high     | power limit  | aux alias   |             |
+--------------------------+--------------------------+--------------+-------------+-------------+

To run the available example:

.. code-block:: bash

    cd examples
    robot robot_test_suite/test_instrument

.. note:: A script demo with all available keywords is under examples/robot_test_suite/test_instrument
    and yaml see robot_inst_aux.yaml!

Acroname Auxiliary
~~~~~~~~~~~~~~~~~~

This plugin can be used to control a acroname usb hub.

Find below an example with all available features:

.. literalinclude:: ../../examples/robot_test_suite/test_acroname/acroname_demo.robot
    :language: robotframework
    :linenos:

To run the available example:

.. code-block:: bash

    cd examples
    robot robot_test_suite/test_instrument

Record Auxiliary
~~~~~~~~~~~~~~~~

Auxiliary used to record a connectors receive channel which are configured
in the yaml config. The library needs then only to be loaded.
See example below:

config.yaml:

.. literalinclude:: ../../examples/record_rtt_segger.yaml
    :language: yaml
    :linenos:

Robot file:

.. literalinclude:: ../../examples/robot_test_suite/test_record/record_demo.robot
    :language: robotframework
    :linenos:


To run the available example:

.. code-block:: bash

    cd examples
    robot robot_test_suite/test_record/

UDS Auxiliary
~~~~~~~~~~~~~

To run the example:

.. literalinclude:: ../../examples/robot_uds.yaml
    :language: yaml
    :linenos:


As the "ITF" uds auxiliary, the robot version integrate exactly the same user's interface.

.. note:: All return types between "ITF" and "Robot" auxiliary's version stay
  identical! Only "Send uds raw" keywords return a list instead of bytes!

Please find below a complete correlation table:

+--------------------------+--------------------------+--------------+-------------+-------------+-------------+
| ITF method               | robot equivalent         | Parameter 1  | Parameter 2 | Parameter 3 | Parameter 4 |
+==========================+==========================+==============+=============+=============+=============+
| send_uds_raw             | Send uds raw             | message      | aux alias   | timeout     |             |
+--------------------------+--------------------------+--------------+-------------+-------------+-------------+
| send_uds_config          | Send uds config          | message      | aux alias   | timeout     |             |
+--------------------------+--------------------------+--------------+-------------+-------------+-------------+

Robot file:

.. literalinclude:: ../../examples/robot_test_suite/test_uds/demo_uds.robot
    :language: robotframework
    :linenos:

To run the available example:

.. code-block:: bash

    cd examples
    robot robot_test_suite/test_uds/


Library Documentation
---------------------

.. automodule:: pykiso.lib.robot_framework.loader
    :members:

.. automodule:: pykiso.lib.robot_framework.aux_interface
    :members:

.. automodule:: pykiso.lib.robot_framework.communication_auxiliary
    :members:

.. automodule:: pykiso.lib.robot_framework.dut_auxiliary
    :members:

.. automodule:: pykiso.lib.robot_framework.proxy_auxiliary
    :members:

.. automodule:: pykiso.lib.robot_framework.instrument_control_auxiliary
    :members:

.. automodule:: pykiso.lib.robot_framework.acroname_auxiliary
    :members:

.. automodule:: pykiso.lib.robot_framework.uds_auxiliary
    :members:
