.. _basic_tests:

Basic test writing
------------------

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

.. note:: User can run several test using several times flag -c. If a folder path is specified,
  a log for each yaml file will be stored. If otherwise a filename is provided, all log information
  will be in one logfile.

.. _define_test_information:

Define the test information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each test fixture (setup, teardown or test_run), users have to define
the test information using the decorator `define_test_parameters`. This decorator
gives access to the following parameters:

- ``suite_id``: current test suite identification number
- ``case_id``: current test case identification number (optional for test suite setup and teardown)
- ``aux_list``: list of used auxiliaries


``suite_id`` and ``case_id`` are used to coordinate and define a clear test execution order.
It is now optional for ``pykiso.BasicTest`` but still mandatory in case of ``pykiso.RemoteTest``.

If both ids are not defined (by default ``suite_id`` and ``case_id`` are equal to 0),
the alphabetical order will be applied on each .py modudle and each contained test class.

In other words, If we have the following test suite folder organisation:

---> test_suite_folder
 |
 ----> a.py module with classes B/C/A (declare in this order)
 |
 ----> b.py module with classes Z/G (declare in this order)
 |
 ----> c.py module with classes S/T + Suite Setup/Teardown

The framework will execute the tests in the below order:

 .. code:: bash

    test_suite_setUp (c.SuiteSetup-0-0)
    test_run (a.A-0-0)
    test_run (a.B-0-0)
    test_run (a.C-0-0)
    test_run (b.G-0-0)
    test_run (b.Z-0-0)
    test_run (c.S-0-0)
    test_run (c.T-0-0)
    test_suite_tearDown (c.SuiteTearDown-0-0)

In order to utilise the SetUp/TearDown test-suite feature, users have to define a class inheriting from
:py:class:`~pykiso.test_coordinator.test_suite.BasicTestSuiteSetup` or
:py:class:`~pykiso.test_coordinator.test_suite.BasicTestSuiteTeardown`.
For each of these classes, the following methods ``test_suite_setUp`` or ``test_suite_tearDown`` must be
overridden with the behaviour you want to have.

.. note::
  | Because the python unittest module is used in the background, all methods
  | starting with "def test_" are executed automatically

.. note::
  If a test in SuiteSetup raises an exception, all tests which belong to the
  same suite_id will be skipped.


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
  """
    @pykiso.define_test_parameters(
            suite_id=1,
            case_id=1,
            aux_list=[aux1, aux2]
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
    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
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

How are the tests called
~~~~~~~~~~~~~~~~~~~~~~~~

Let us imagine we have 2 test-cases which are part of a test-suite.

.. code:: python

    import pykiso
    from pykiso.auxiliaries import aux1, aux2

    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
    class SuiteSetup(pykiso.BasicTestSuiteSetup):
        pass

    @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
    class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
        pass

    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[aux1])
    class TestCase1(pykiso.BasicTest):
        def setUp(self):
            pass
        def test_run_1(self):
            pass
        def test_run_2(self):
            pass
        def tearDown(self):
            pass

    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[aux1])
    class TestCase2(pykiso.BasicTest):
        def setUp(self):
            pass
        def test_run_1(self):
            pass
        def test_run_2(self):
            pass
        def tearDown(self):
            pass

The pykiso will call the elements in the following order:

.. code:: bash

    TestSuiteSetup().test_suite_setUp
    TestCase1.setUpClass
        TestCase1().setUp
        TestCase1().test_run
        TestCase1().tearDown
        TestCase1().setUp
        TestCase1().test_run_2
        TestCase1().tearDown
    TestCase1.tearDownClass
    TestCase2.setUpClass
        TestCase2().setUp
        TestCase2().test_run
        TestCase2().tearDown
        TestCase2().setUp
        TestCase2().test_run_2
        TestCase2().tearDown
    TestCase2.tearDownClass
    TestSuiteTeardown().test_suite_tearDown


To learn more, please take a look at :ref:`advanced_tests`.
