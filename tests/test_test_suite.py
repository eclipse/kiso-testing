import pytest
import unittest

"""Fake test case write into fake_suite_1.py containing 
one test case PASS and one FAILED.
"""
EX_TEST_CASE = """
import unittest
import pykiso
import logging

@pykiso.define_test_parameters(suite_id=1, case_id=0, aux_list=[])
class FakeTestCase(pykiso.BasicTestSuiteSetup):

    def test_fake_1(self):
        logging.info("I HAVE RUN A FAKE TEST CASE")
        self.assertEqual(1,1)

    def test_fake_2(self):
        logging.info("I HAVE RUN A SECOND FAKE TEST CASE")
        self.assertEqual(1,2)
"""

@pytest.mark.usefixtures("CustomTestCaseAndSuite")
class IntegrationTestSuite(unittest.TestCase):
    test_suite_directory = None
    test_case_file = None

    @pytest.fixture(autouse=True)
    def init_suite_directory(self, tmpdir):
        """Create a folder in temporary location named fake_suite_1 and 
        add fake_suite_1.py  with EX_TEXT_CASE fake test
        """
        IntegrationTestSuite.test_suite_directory = tmpdir.mkdir("fake_suite_1")
        IntegrationTestSuite.test_case_file = IntegrationTestSuite.test_suite_directory.join("fake_suite_1.py")
        IntegrationTestSuite.test_case_file.write(EX_TEST_CASE)

    def test_load_test_suite(self):
        """Run a test suite sub class from test_suite.BasicTestSuite (see conftest.py).

        Validation criteria:
        -  sub class from test_suite.BasicTestSuit behave like unittest.TestSuite
        -  no error are reported
        -  1 failure is reported
        -  failed test id is 'fake_suite_1.FakeTestCase.test_fake_2'
        -  no test case are skipped
        -  number of test run equal to 4
        """
        parameters = (IntegrationTestSuite.test_suite_directory, "*.py", 1, [], {})
        
        self.init.prepare_default_test_suites(parameters)
        result = unittest.TextTestRunner().run(self.init.custom_test_suite)

        self.assertEqual(result.wasSuccessful(), False)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0][0].id(),'pykiso.test_case.define_test_parameters.<locals>.generate_modified_class.<locals>.NewClass.test_fake_2')
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 3)