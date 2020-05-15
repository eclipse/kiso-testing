import pytest
import unittest

import sys

@pytest.mark.usefixtures("CustomTestCaseAndSuite")
class IntegrationTestCase(unittest.TestCase):

    def test_load_test_case(self):
        """run a default test case (see conftest.py), using existing auxiliaries
        (ExampleAuxiliary) and connectors (CCExample)

        Validation criteria:
        -  sub class from test_case.BasicTest behave like unittest.TestCase
        -  all test ares PASSED
        -  no error are reported
        -  no failure is reported
        -  no test case are skipped
        -  number of test run equal to len of parameters set
        """
        self.init.create_communication_pipeline(3)
        parameters = [(1, 1, self.init.auxiliaries),
                      (1, 2, [self.init.auxiliaries[0]]),
                      (2, 3, [self.init.auxiliaries[1]]),
                      (1, 4, [self.init.auxiliaries[2]]),
                      (0, 5, self.init.auxiliaries[0:2])]

        for params in parameters :
            self.init.prepare_default_test_cases(params)

        runner = unittest.TextTestRunner()
        result = runner.run(self.init.suite)
        self.init.stop()

        self.assertEqual(result.wasSuccessful(), True)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, len(parameters))