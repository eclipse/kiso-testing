.. _advanced_tests:

How to make the most of the tests
---------------------------------

Define the test information (in addition)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to link the architecture requirement to the test,
an additional reference can be added into the test_run decorator:

- ``test_ids``: optional requirements linked to the test that need to be defined as follow:

.. code:: python

    {"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}

In order to run only a subset of tests, an additional reference can be added to the test_run decorator:

- tag : [optional] the variant can be defined like:

.. code:: python

    {"variant": ["variant2", "variant1"], "branch_level": ["daily", "nightly"]}

Both parameters (variant/branch_level), will play the role of filter to fine
tune the test collection and at the end ensure the execution of very specific tests subset.

.. note:: cli tags must be given in pairs. If one key has multiple values seperate them with a comma

.. code:: bash

    pykiso -c configuration_file --variant var1,var2 --branch-level daily,nightly

.. table:: Exectuion table for test case tags and cli tag arguments
   :widths: auto

   =======================================================  ===============================  ========
   test case tags                                           cli tags                         executed
   =======================================================  ===============================  ========
   "branch_level": ["daily","nightly"]                      branch_level nightly             🗸
   "branch_level": ["daily","nightly"]                      branch_level nightly,daily       🗸
   "branch_level": ["daily","nightly"]                      branch_level master              ✗
   "branch_level": ["daily","nightly"],"variant":["var1"]   branch_level nightly             🗸
   "branch_level": ["daily","nightly"],"variant":["var1"]   variant var1                     🗸
   "branch_level": ["daily","nightly"],"variant":["var1"]   variant var2                     ✗
   "branch_level": ["daily","nightly"],"variant":["var1"]   branch_level daily variant var1  ✗
   =======================================================  ===============================  ========

Find below a full example for a test suite/case declaration :

.. code:: python

  """
  Add test suite setup fixture, run once at test suite's beginning.
  Test Suite Setup Information:
  -> suite_id : set to 1
  -> case_id : Parameter case_id is not mandatory for setup.
  -> aux_list : used aux1 and aux2 is used
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
    class SuiteSetup(pykiso.BasicTestSuiteSetup):
        def test_suite_setUp():
            logging.info("I HAVE RUN THE TEST SUITE SETUP!")
            if aux1.not_properly_configured():
                aux1.configure()
            aux2.configure()
            callback_registering()

  """
  Add test suite teardown fixture, run once at test suite's end.
  Test Suite Teardown Information:
  -> suite_id : set to 1
  -> case_id : Parameter case_id is not mandatory for setup.
  -> aux_list : used aux1 and aux2 is used
  """
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
    class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
        def test_suite_tearDown():
            logging.info("I HAVE RUN THE TEST SUITE TEARDOWN!")
            callback_unregistering()

  """
  Add a test case 1 from test suite 1 using auxiliary 1.
    Test Suite Teardown Information:
  -> suite_id : set to 1
  -> case_id : set to 1
  -> aux_list : used aux1 and aux2 is used
  -> test_ids: [optional] store the requirements into the report
  -> tag: [optional] dictionary containing lists of variants and/or test levels when only a subset of tests needs to be executed
  """
    @pykiso.define_test_parameters(
            suite_id=1,
            case_id=1,
            aux_list=[aux1, aux2],
            test_ids={"Component1": ["Req1", "Req2"]},
            tag={"variant": ["variant2", "variant1"], "branch_level": ["daily", "nightly"]},
    )
    class MyTest(pykiso.BasicTest):
        pass

Implementation of Advanced Tests - Auxiliary Interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the dynamic importing capabilities of the framework we can interact with the auxiliaries directly.

For this test we will assume that we have configured a
:py:class:`~pykiso.lib.auxiliaries.communication_auxiliary.CommunicationAuxiliary`
and a connector that supports `raw` messaging.


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


We can use the configured and instantiated auxiliary ``com_aux`` (imported by it's alias) in the test directly.

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
   **auxiliary**(in that case use RemoteTest instead of BasicTest)

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


Implementation of Advanced Tests - Repeat testCases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pykiso.retry_test_case
    :members:

**test_suite_1.py**:

.. code:: python

    # define an external iterator that can be used for retry_test_case demo
    side_effect = cycle([False, False, True])

    @pykiso.define_test_parameters()
    class MyTest1(pykiso.BasicTest):
        """This test case definition will override the setUp, test_run and tearDown method."""

        @pykiso.retry_test_case(max_try=3)
        def setUp(self):
            """Hook method from unittest in order to execute code before test case run.
            In this case the default setUp method is overridden, allowing us to apply the
            retry_test_case's decorator. The syntax super() access to the BasicTest and
            we will run the default setUp()
            """
            super().setUp()

        @pykiso.retry_test_case(max_try=5, rerun_setup=True, rerun_teardown=False)
        def test_run(self):
            """In this case the default test_run method is overridden and
            instead of calling test_run from BasicTest class the following
            code is called.

            Here, the test pass at the 3rd attempt out of 5. The setup and
            tearDown methods are called for each attempt.
            """
            logging.info(
                f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
            )
            self.assertTrue(next(side_effect))
            logging.info(f"I HAVE RUN 0.1.1 for variant {self.variant}!")

        @pykiso.retry_test_case(max_try=3, stability_test=True)
        def tearDown(self):
            """Hook method from unittest in order to execute code after the test case ran.
            In this case the default tearDown method is overridden, allowing us to apply the
            retry_test_case's decorator. The syntax super() access to the BasicTest and
            we will run the default tearDown().

            The retry_test_case has stability test activated, so the tearDown method will
            be run 3 times.
            """
            super().tearDown()


.. _run_the_tests:

Test verbosity
~~~~~~~~~~~~~~

``pykiso -c <config_file>``

To let the user decide which information they want to see in their logs, new log levels
have been defined. When launched normally, only the logs from the tests and the framework
errors will be active.
The option -v (--verbose) should be used to display the internal logs of the framework:

``pykiso -c <config_file> -v``

or

``pykiso -c <config_file> --verbose``

Three internal log levels are available: INTERNAL_INFO, INTERNAL_DEBUG, INTERNAL_WARNING.
They will then be activated depending on the value of the--log-level option. Error logs
level will always be logged, internal or not.

The summary of the activated logs depending of the value of the --log-level and
--verbose options can be found in the following table:

+------------------------+-----------------------------+--------------------+
|                        | verbose == True             | verbose == False   |
|                        |                             |                    |
+========================+=============================+====================+
| log-level == DEBUG     |DEBUG, INTERNAL_DEBUG,       |DEBUG, INFO,        |
|                        |INFO, INTERNAL_INFO, WARNING,|WARNING, ERROR      |
|                        |INTERNAL_WARNING, ERROR      |                    |
+------------------------+-----------------------------+--------------------+
| log-level == INFO      |INFO, INTERNAL_INFO,         |INFO, WARNING,      |
|                        |WARNING, INTERNAL_WARNING,   |ERROR               |
|                        |ERROR                        |                    |
+------------------------+-----------------------------+--------------------+
| log-level == WARNING   |WARNING, INTERNAL_WARNING,   |WARNING, ERROR      |
|                        |ERROR                        |                    |
+------------------------+-----------------------------+--------------------+
| log-level == ERROR     |ERROR                        |ERROR               |
+------------------------+-----------------------------+--------------------+


.. _test_case_patterns:

Run single tests
~~~~~~~~~~~~~~~~

Test case can be selected with the -p or --pattern flag.
Here is an example to just override the test file:

.. code:: bash

    pykiso -c dummy.yaml -p test_suite_1.py



It is also possible to select single or multiple test cases by extending the pattern.
Test classes and single test methods can be selected.
The pattern can consist 3 elements separated by a "::".
Each element is a unix file name pattern.

The elements are file_name::test_class_name::test_method_name

Here some examples:

.. code:: bash


    #select a single test
    pykiso -c dummy.yaml -p test_suite_1.py::TestClass::test_run1

    #select all test methods which begins with test_
    pykiso -c dummy.yaml -p test_suite_1.py::TestClass::test_*

    #select all test classes which starts with Test and run method test_run1
    pykiso -c dummy.yaml -p test_suite_1.py::Test*::test_run1

    #use file pattern from yaml file and select all test classes and run method test_run1
    pykiso -c dummy.yaml -p ::*::test_run1
