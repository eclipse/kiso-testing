Remote Test
===========

With the remote test approach, the idea is to execute tests on the targeted hardware to enable 
the developer to practice test-driven-development directly on the target.


Test Coordinator
~~~~~~~~~~~~~~~~

In the case of remote tests usage, the **test-coordinator** will still perform the same task 
but will also:

-  verify if the tests can be performed
-  flash and run and synchronize the tests on the *device under test*

Auxiliary
~~~~~~~~~

For the remote test approach, auxiliaries should be composed by 2 blocks:

-  physical or digital instance creation / deletion (e.g. flash the
   *device under test* with the testing software, e.g. Start a docker
   container)
-  connectors to facilitate interaction and communication with the
   device (e.g. flashing via *JTAG*, messaging with *UART*)
  
One example of implementation of such an auxiliary is the *device under test* auxiliary used with the TestApp.
In this specific case we have:
 
  -  As communication channel (**cchannel**) usually *UART*
  -  As flashing channel (**flashing**) usually *JTAG*


Connector
~~~~~~~~~

Communication Channel
^^^^^^^^^^^^^^^^^^^^^

In case of the *device under test*, we have a specific communication protocol. Please see the next paragraph.

Flashing
^^^^^^^^

The Flasher Connectors usually provide only one method, :py:meth:`Flasher.flash`, which will transfer the configured binary file to the target.


.. _flashing-1:


Message Protocol 
~~~~~~~~~~~~~~~~

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


Flashing
~~~~~~~~

The flashing is usually needed to put the test-software containing the tests we would like to run into the *Device under test* .
Flashing is done via a flashing connector, which has to be configured with the correct binary file.
The flashing connector is in turn called from an appropriate auxiliary (usually in its setup phase).


Implementation of Remote Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For remote tests, RemoteTestCase / RemoteTestSuite should be used instead of BasicTestCase / BasicTestSuite, based on Message Protocol, 
users can configure the maximum time (in seconds) used to wait for a report.
This "timeout" is configurable for each available fixtures :

- setup_timeout : the maximum time (in seconds) used to wait for a report during setup execution (optional)
- run_timeout : the maximum time (in seconds) used to wait for a report during test_run execution (optional)
- teardown_timeout : the maximum time (in seconds) used to wait for a report during teardown execution (optional)

.. note:: by default those timeout values are set to 10 seconds.


Find below a full example for a test suite/case declaration in case the Message Protocol / TestApp is used:

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
    class SuiteSetup(pykiso.RemoteTestSuiteSetup):
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
    class SuiteTearDown(pykiso.RemoteTestSuiteTeardown):
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
  -> tag: [optional] dictionary containing lists of variants and/or test levels when only a subset of tests needs to be executed
  """
    @pykiso.define_test_parameters(
            suite_id=1,
            case_id=1,
            aux_list=[aux1, aux2],
            setup_timeout=3,
            run_timeout=10,
            teardown_timeout=3,
            test_ids={"Component1": ["Req1", "Req2"]},
            tag={"variant": ["variant2", "variant1"], "branch_level": ["daily", "nightly"]},
    )
    class MyTest(pykiso.RemoteTest):
        pass


Config File for remote tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For details see :ref:`../getting_started/config_file`.

Find below an example of config for used for remote testing (is that case using *device under test* auxiliary)

.. literalinclude:: ../../examples/fdx_lauterbach.yaml
    :language: yaml
    :linenos:
