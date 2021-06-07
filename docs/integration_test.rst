Integration Test Framework Developer’s Guide
============================================

Introduction
------------

The Integration Test Framework provides the possibility to write and run
tests on a HW target. It is built to orchestrate the entities and
services involved in the tests. The framework can be used for both
white-box and black-box testing as well as in the integration and system
testing.

Design Overview
---------------

.. figure:: images/pykiso_context_overview.png
   :alt: Figure 1: Integration Test Framework Context

   Figure 1: Integration Test Framework Context

The *pykiso* Testing Framework is built in a modular and configurable
way with abstractions both for entities (e.g. a handler for the device
under test) and communication (e.g. UART or TCP/IP).

The tests leverage the python *unittest*-Framework which has a similar
flavor as many available major unit testing frameworks and thus comes
with an ecosystem of tools and utilities.

Test Coordinator
~~~~~~~~~~~~~~~~

The **test-coordinator** is the central module setting up and running
the tests. Based on a configuration file (in YAML), it does the
following:

-  instantiate the selected connectors
-  instantiate the selected auxiliaries
-  provide the auxiliaries with the matching connectors
-  generate the list of tests to perform
-  provide the testcases with the auxiliaries they need
-  verify if the tests can be performed
-  flash and run and synchronize the tests on the auxiliaries
-  gather the reports and publish the results

Auxiliary
~~~~~~~~~

The **auxiliary** provides to the **test-coordinator** an interface to
interact with the physical or digital auxiliary target. It is composed
by 2 blocks:

-  physical or digital instance creation / deletion (e.g. flash the
   *device under test* with the testing software, e.g. Start a docker
   container)
-  connectors to facilitate interaction and communication with the
   device (e.g. flashing via *JTAG*, messaging with *UART*)

In case of the specific *device under test* auxiliary, we have:

-  As communication channel (**cchannel**) usually *UART*
-  As flashing channel (**flashing**) usually *JTAG*

For other auxiliaries like the one interacting with cloud services,
maybe we just have:

-  A communication channel (**channel**) like *REST*

Connector
~~~~~~~~~

Communication Channel
^^^^^^^^^^^^^^^^^^^^^

The Communication Channel - also known as **cchannel** - is the medium
to communicate with auxiliary target. Example include *UART*, *UDP*,
*USB*, *REST*,… The communication protocol itself can be auxiliary
specific. In case of the *device under test*, we have a specific
communication protocol. Please see the next paragraph.

Flashing
^^^^^^^^

The Flasher Connectors usually provide only one method, :py:meth:`Flasher.flash`, which will transfer the configured binary file to the target.

Dynamic Import Linking
~~~~~~~~~~~~~~~~~~~~~~

The `pykiso` framework was developed with modularity and reusability in mind.
To avoid close coupling between testcases and auxiliaries as well as between auxiliaries and connectors, the linking between those components is defined in a config file (see :ref:`config_file`) and performed by the `TestCoordinator`.

Different instances of connectors and auxiliaries are given *aliases* which identify them within the test session.

Let's say we have this (abridged) config file:

.. code:: yaml

    connectors:
      my_chan:           # Alias of the connector
        type: ...
    auxiliaries:
      my_aux:            # Alias of the auxiliary
        connectors:
            com: my_chan # Reference to the connector
        type: ...

The auxiliary `my_aux` will automatically be initialised with `my_chan` as its `com` channel.

When writing your testcases, the auxiliary will then be available under its defined alias.

.. code:: python

    from pykiso.auxiliaries import my_aux

The `pykiso.auxiliaries` is a magic package that only exists in the `pykiso` package after the `TestCoordinator` has processed the config file.
It will include all *instances* of the defined auxiliares, available at their defined alias.

Message Protocol ( If in used )
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The message protocol is used (but not only) between the *device under
test* HW and its **test-auxiliary**. The communication pattern is as
follows:

1. The test manager sends a message that contains a test command to a
   test participant.
2. The test participant sends an acknowledgement message back.
3. The test participant may send a report message.
4. The test manager replies to a report message with an acknowledgement
   message.

The message structure is as follow:

::

   0               1               2               3
   0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Ver| MT|  Res  |   Msg Token   |   Sub-Type    | Error code    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Test Section  |  Test Suite   |   Test Case   | Payload length|
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Payload (in TLV format)
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

It consist of:

+----------------------------------+--------------------+-------------+
| Code                             | size (in bytes)    | Explanation |
+==================================+====================+=============+
| Ver (Version)                    | 2 bits             | Indicates   |
|                                  |                    | the version |
|                                  |                    | of the test |
|                                  |                    | c           |
|                                  |                    | oordination |
|                                  |                    | protocol.   |
+----------------------------------+--------------------+-------------+
| MT (Message Type)                | 2 bits             | Indicates   |
|                                  |                    | the type of |
|                                  |                    | the         |
|                                  |                    | message.    |
+----------------------------------+--------------------+-------------+
| Res (Reserved)                   | 4 bits             |             |
+----------------------------------+--------------------+-------------+
| Msg Token (Message Token)        | 1                  | Arbitrary   |
|                                  |                    | byte. It    |
|                                  |                    | must not be |
|                                  |                    | repeated    |
|                                  |                    | for 10      |
|                                  |                    | consecutive |
|                                  |                    | messages.   |
|                                  |                    | In the      |
|                                  |                    | ackn        |
|                                  |                    | owledgement |
|                                  |                    | message the |
|                                  |                    | same token  |
|                                  |                    | must be     |
|                                  |                    | used.       |
+----------------------------------+--------------------+-------------+
| Sub-Type (Message Sub Type)      | 1                  | Gives more  |
|                                  |                    | information |
|                                  |                    | about the   |
|                                  |                    | message     |
|                                  |                    | type        |
+----------------------------------+--------------------+-------------+
| Error Code                       | 1                  | Error code  |
|                                  |                    | that can be |
|                                  |                    | used by the |
|                                  |                    | auxiliaries |
|                                  |                    | to forward  |
|                                  |                    | an error    |
+----------------------------------+--------------------+-------------+
| Test Section                     | 1                  | Indicates   |
|                                  |                    | the test    |
|                                  |                    | section     |
|                                  |                    | number      |
+----------------------------------+--------------------+-------------+
| Test Suite                       | 1                  | Indicates   |
|                                  |                    | the test    |
|                                  |                    | suite       |
|                                  |                    | number      |
|                                  |                    | which       |
|                                  |                    | permits to  |
|                                  |                    | identify a  |
|                                  |                    | test suite  |
|                                  |                    | within a    |
|                                  |                    | test        |
|                                  |                    | section     |
+----------------------------------+--------------------+-------------+
| Test Case                        | 1                  | Indicates   |
|                                  |                    | the test    |
|                                  |                    | case number |
|                                  |                    | which       |
|                                  |                    | permits to  |
|                                  |                    | identify a  |
|                                  |                    | test case   |
|                                  |                    | within a    |
|                                  |                    | test suite  |
+----------------------------------+--------------------+-------------+
| Payload Length                   | 1                  | Indicate    |
|                                  |                    | the length  |
|                                  |                    | of the      |
|                                  |                    | payload     |
|                                  |                    | composed of |
|                                  |                    | TLV         |
|                                  |                    | elements.   |
|                                  |                    | If 0, it    |
|                                  |                    | means there |
|                                  |                    | is no       |
|                                  |                    | payload     |
+----------------------------------+--------------------+-------------+
| Payload                          | X                  | Optional,   |
|                                  |                    | list of     |
|                                  |                    | TLVs        |
|                                  |                    | elements.   |
|                                  |                    | One TLV has |
|                                  |                    | 1 byte for  |
|                                  |                    | the *Tag*,  |
|                                  |                    | 1 byte for  |
|                                  |                    | the         |
|                                  |                    | *length*,   |
|                                  |                    | up to 255   |
|                                  |                    | bytes for   |
|                                  |                    | the *Value* |
+----------------------------------+--------------------+-------------+

The **message type** and **message sub-type** are linked and can take
the following values:

+---------+---------+---------------------+-------------+-----------+
| Type    | Type Id | Sub-type            | Sub-type Id | Ex        |
|         |         |                     |             | planation |
+=========+=========+=====================+=============+===========+
| COMMAND | 0       | PING                | 0           | For       |
|         |         |                     |             | ping-pong |
|         |         |                     |             | between   |
|         |         |                     |             | the       |
|         |         |                     |             | auxiliary |
|         |         |                     |             | to verify |
|         |         |                     |             | if a      |
|         |         |                     |             | comm      |
|         |         |                     |             | unication |
|         |         |                     |             | is        |
|         |         |                     |             | es        |
|         |         |                     |             | tablished |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_SECTION_SETUP  | 1           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_SUITE_SETUP    | 2           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_CASE_SETUP     | 3           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_SECTION_RUN    | 11          |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_SUITE_RUN      | 12          |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_CASE_RUN       | 13          |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TE                  | 21          |           |
|         |         | ST_SECTION_TEARDOWN |             |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_SUITE_TEARDOWN | 22          |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_CASE_TEARDOWN  | 23          |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | ABORT               | 99          |           |
+---------+---------+---------------------+-------------+-----------+
| REPORT  | 1       | TEST_PASS           | 0           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_FAILED         | 1           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | TEST_NOT_IMPLEMENTED| 2           |           |
+---------+---------+---------------------+-------------+-----------+
| ACK     | 2       | ACK                 | 0           |           |
+---------+---------+---------------------+-------------+-----------+
|         |         | NACK                | 1           |           |
+---------+---------+---------------------+-------------+-----------+
| LOG     | 3       | RESERVED            | 0           |           |
+---------+---------+---------------------+-------------+-----------+


The TLV only supported *Tag* are:

-  TEST_REPORT = 110
-  FAILURE_REASON = 112

.. _flashing-1:

Flashing
~~~~~~~~

The flashing is usually needed to put the test-software containing the tests we would like to run into the *Device under test* .
Flashing is done via a flashing connector, which has to be configured with the correct binary file.
The flashing connector is in turn called from an appropriate auxiliary (usually in its setup phase).

Usage
-----

Flow
~~~~

1. Create a root-folder that will contain the tests. Let us call it
   *test-folder*.
2. Create, based on your test-specs, one folder per test-suite.
3. In each test-suite folder, implement the tests. (See how below)
4. write a configuration file (see :ref:`config_file`)
5. If your test-setup is ready, run
   ``pykiso -c <ROOT_TEST_DIR>``
6. If the tests fail, you will see it in the the output. For more
   details, you can take a look at the log file (logs to STDOUT as default).

Define the test information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each test fixture (setup, teardown or test_run), users have to define
the test information using the decorator define_test_parameters. This decorator
gives access to the following parameters:

- suite_id : current test suite identification number
- case_id : current test case identification number (optional for test suite setup and teardown)
- aux_list : list of used auxiliaries

Based on Message Protocol, users can configure the maximum time (in seconds) used to wait for a report.
This "timeout" is configurable for each available fixtures :

- setup_timeout : the maximum time (in seconds) used to wait for a report during setup execution (optional)
- run_timeout : the maximum time (in seconds) used to wait for a report during test_run execution (optional)
- teardown_timeout : the maximum time (in seconds) used to wait for a report during teardown execution (optional)

.. note:: by default those timeout values are set to 10 seconds.

In order to link the architecture requirement to the test,
an additional reference can be added into the test_run decorator:
-  test_ids: [optional] requirements has to be defined like follow:

{"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}

Find below a full example for a test suite/case declaration :

.. code:: python

  """
  Add test suite setup fixture, run once at test suite's beginning.
  Test Suite Setup Information:
  -> suite_id : set to 1
  -> case_id : Parameter case_id is not mandatory for setup.
  -> aux_list : used aux1 and aux2 is used
  -> setup_timeout : time to wait for a report 5 seconds
  -> run_timeout : Parameter run_timeout is not mandatory for test suite setup.
  -> teardown_timeout : Parameter run_timeout is not mandatory for test suite setup.
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], setup_timeout=5)
    class SuiteSetup(pykiso.BasicTestSuiteSetup):
        pass

  """
  Add test suite teardown fixture, run once at test suite's end.
  Test Suite Teardown Information:
  -> suite_id : set to 1
  -> case_id : Parameter case_id is not mandatory for setup.
  -> aux_list : used aux1 and aux2 is used
  -> setup_timeout : Parameter run_timeout is not mandatory for test suite teardown.
  -> run_timeout : Parameter run_timeout is not mandatory for test suite teardown.
  -> teardown_timeout : time to wait for a report 5 seconds
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], teardown_timeout=5,)
    class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
        pass

  """
  Add a test case 1 from test suite 1 using auxiliary 1.
    Test Suite Teardown Information:
  -> suite_id : set to 1
  -> case_id : set to 1
  -> aux_list : used aux1 and aux2 is used
  -> setup_timeout : time to wait for a report 3 seconds during setup
  -> run_timeout : time to wait for a report 10 seconds during test_run
  -> teardown_timeout : time to wait for a report 3 seconds during teardown
  -> test_ids: [optional] store the requirements into the report
  """
    @pykiso.define_test_parameters(
            suite_id=1, case_id=1, aux_list=[aux1, aux2], setup_timeout=3,
            run_timeout=10, teardown_timeout=3,
            test_ids={"Component1": ["Req1", "Req2"]}
    )
    class MyTest(pykiso.BasicTest):
        pass


Implementation of Basic Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Structure**: *test-folder*/*test-suite-1*/**test_suite_1.py**

**test_suite_1.py**:

.. code:: python

   """
   I want to run the following tests documented in the following test-specs <TEST_CASE_SPECS>.
   """
    import pykiso
    from pykiso.auxiliaries import aux1, aux2

  """
  Add test suite setup fixture, run once at test suite's beginning.
  Parameter case_id is not mandatory for setup.
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2], setup_timeout=1, run_timeout=2, teardown_timeout=3)
    class SuiteSetup(pykiso.BasicTestSuiteSetup):
        pass

  """
  Add test suite teardown fixture, run once at test suite's end.
  Parameter case_id is not mandatory for teardown.
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
    class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
        pass

  """
  Add a test case 1 from test suite 1 using auxiliary 1.
  """
    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[aux1])
    class MyTest(pykiso.BasicTest):
        pass

  """
  Add a test case 2 from test suite 1 using auxiliary 2.
  """
    @pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=[aux2])
    class MyTest2(pykiso.BasicTest):
        pass

Implementation of Advanced Tests - Auxiliary Interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the dynamic importing capabilities of the framework we can interact with the auxiliaries directly.

For this test we will assume that we have configured a :py:class:`pykiso.lib.auxiliaries.communication_auxiliary.CommunicationAuxiliary` and a connector that supports `raw` messaging.


.. code:: python

    """
    send a message, receive a response, compare to expected response
    """
    import pykiso
    from pykiso.auxiliaries import com_aux

    @pykiso.define_test_parameters(suite_id=2, case_id=1, aux_list=[com_aux])
    class ComTest(pykiso.BasicTest):

        STIMULUS = b"stimulus message"
        RESPONSE = b"expected reply"

        def test_run(self):
            com_aux.send_message(STIMULUS)
            resp = com_aux.receive_message()
            self.assertEqual(resp, RESPONSE)


We can use the configured and instantiated auxiliary `com_aux` (imported by it's alias) in the test directly.

Implementation of Advanced Tests - Custom Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to have more complex tests, you can do the following:

-  ``BasicTest`` is a specific implementation of ``unittest.TestCase``
   therefore it contains 3 steps/methods **setUp()**, **tearDown()** and
   **test_run()** that can be overwritten.
-  ``BasicTest`` will contain the list of **auxiliaries** you can use.
   It will be hold in the attribute ``test_auxiliary_list``.
-  ``BasicTest`` also contains the following information
   ``test_section_id``, ``test_suite_id``, ``test_case_id``.
-  Import *logging* or/and *message* (if needed) to communicate with the
   **auxiliary**

**test_suite_2.py**:

.. code:: python

    """
    I want to run the following tests documented in the following test-specs <TEST_CASE_SPECS>.
    """
    import pykiso
    from pykiso import message
    from pykiso.auxiliaries import aux1


    @pykiso.define_test_parameters(suite_id=2, case_id=1, aux_list=[aux1])
    class MyTest(pykiso.BasicTest):
        def setUp(self):
           # I loop through all the auxiliaries
           for aux in self.test_auxiliary_list:
               if aux.name == "aux1": # If I find the auxiliary to which I need to send a special message, I compose the message and send it.
                   # Compose the message to send with some additional information
                   tlv = { TEST_REPORT:"Give me something" }
                   testcase_setup_special_message = message.Message(msg_type=message.MessageType.COMMAND, sub_type=message.MessageCommandType.TEST_CASE_SETUP,
                                                           test_section=self.test_section_id, test_suite=self.test_suite_id, test_case=self.test_case_id, tlv_dict=tlv)
                   # Send the message
                   aux.run_command(testcase_setup_special_message, blocking=True, timeout_in_s=10)
               else: # Do not forget to send a setup message to the other auxiliaries!
                   # Compose the normal message
                   testcase_setup_basic_message = message.Message(msg_type=message.MessageType.COMMAND, sub_type=message.MessageCommandType.TEST_CASE_SETUP,
                                                           test_section=self.test_section_id, test_suite=self.test_suite_id, test_case=self.test_case_id)
                   # Send the message
                   aux.run_command(testcase_setup_basic_message, blocking=True, timeout_in_s=10)

.. _implementation-of-the-tests-advance-1:

Implementation of Advanced Tests - Test Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because we are python based, you can until some extend, design and
implement parts of the framework to fulfil your needs. For example:

**test_suite_3.py**:

.. code:: python

    import pykiso
    from pykiso import message
    from pykiso.auxiliaries import aux1


    class MyTestTemplate(pykiso.BasicTest):
       def test_run(self):
           # Prepare message to send
           testcase_run_message = message.Message(msg_type=message.MessageType.COMMAND, sub_type=message.MessageCommandType.TEST_CASE_RUN,
                                                       test_section=self.test_section_id, test_suite=self.test_suite_id, test_case=self.test_case_id)
           # Send test start through all auxiliaries
           for aux in self.test_auxiliary_list:
               if aux.run_command(testcase_run_message, blocking=True, timeout_in_s=10) is not True:
                   self.cleanup_and_skip("{} could not be run!".format(aux))
           # Device will reboot, wait for the reboot report
           for aux in self.test_auxiliary_list:
               if aux.name == "DeviceUnderTest":
                   report = aux.wait_and_get_report(blocking=True, timeout_in_s=10) # Wait for a report from the DeviceUnderTest
                   break
           # Check if the report for the reboot was received.
           report is not None and report.get_message_type() == message.MessageType.REPORT and report.get_message_sub_type() == message.MessageReportType.TEST_PASS:
               pass # We can continue
           else:
               self.cleanup_and_skip("Device failed rebooting")
           # Loop until all reports are received
           list_of_aux_with_received_reports = [False]*len(self.test_auxiliary_list)
           while False in list_of_aux_with_received_reports:
               # Loop through all auxiliaries
               for i, aux in enumerate(self.test_auxiliary_list):
                   if list_of_aux_with_received_reports[i] == False:
                       # Wait for a report
                       reported_message = aux.wait_and_get_report()
                       # Check the received message
                       list_of_aux_with_received_reports[i] = self.evaluate_message(aux, reported_message)

    @pykiso.define_test_parameters(suite_id=3, case_id=1, aux_list=[aux1])
    class MyTest(MyTestTemplate):
       pass

    @pykiso.define_test_parameters(suite_id=3, case_id=2, aux_list=[aux1])
    class MyTest2(MyTestTemplate):
       pass


Add Config File
~~~~~~~~~~~~~~~

For details see :ref:`config_file`.

Example:

.. literalinclude:: ../examples/dummy.yaml
    :language: yaml
    :linenos:

Run the tests
~~~~~~~~~~~~~

``pykiso -c <config_file>``
