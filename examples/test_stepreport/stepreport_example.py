##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
test_suite_1
************
:module: test_suite_1
:synopsis: Basic example on how to write and configure test suite and
case on ITF side in order to communicate with the device under test
using TestApp.
"""

import importlib
import logging
from itertools import cycle

import pykiso


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
)
class StepReportTest(pykiso.BasicTest):
    """This example demonstrates the step report"""

    def setUp(self):
        """Set header information and check setup conditions"""
        super().setUp()
        self.assertTrue(True, msg="Check my device is ready")
        # additional data to include in the step-report
        self.step_report.header["Version_device"] = "2022-1234"

    def test_run(self):
        """In this case the default test_run method is overridden and
        instead of calling test_run from RemoteTest class the following
        code is called.
        Here, the test pass at the 3rd attempt out of 5. The setup and
        tearDown methods are called for each attempt.
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # data to test
        device_on = True
        voltage = 3.8

        self.assertTrue(device_on, msg="Check my device is ready")

        with self.subTest("Non critical checks"):
            # This check will fail but the test continues
            self.assertFalse(device_on, msg="Some check")

        # assert with custom message
        # assert msg overwritten when step_report_message not null
        self.step_report.message = "Custom message"
        self.assertAlmostEqual(voltage, 4, delta=1, msg="Check voltage device")
        # Custom message is reset there
        self.assertAlmostEqual(voltage, 4, delta=1, msg="Check voltage device")

        logging.info(f"I HAVE RUN 0.1.1 for tag {self.tag}!")


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=2,
)
class TableTest(pykiso.BasicTest):
    """This test shows multiple tables in the step report"""

    def setUp(self):
        """Set header information and check setup conditions"""
        super().setUp()
        # additional data to include in the step-report
        self.step_report.header["Version_device"] = "2022-1234"

    def test_run(self):
        """In this test we specify custom tables to group the steps."""
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        # data to test
        device_on = True
        voltage = 3.8

        self.step_report.current_table = "First table"

        self.assertTrue(device_on, msg="Check my device is ready")

        self.step_report.current_table = "Another table"

        with self.subTest("Non critical checks"):
            # This check will fail but the test continues
            self.assertFalse(device_on, msg="Some check")

        self.step_report.current_table = "Last table"

        # Assert with custom message
        # Assert msg overwritten when step_report_message not null
        self.step_report.message = "Custom message"
        self.assertAlmostEqual(voltage, 4, delta=1, msg="Check voltage device")

        logging.info(f"I HAVE RUN 0.1.1 for tag {self.tag}!")


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=3,
)
class WrapLongTextTest(pykiso.BasicTest):
    """This test shows wrapping of long results into foldable html elements"""

    def setUp(self):
        """Set header information and check setup conditions"""
        super().setUp()
        # additional data to include in the step-report
        self.step_report.header["Version_device"] = "2022-1234"

    def test_run(self):
        """Write long results to the step report to show how foldable html
        elements get used to make the report overview more readable
        """
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
        # since we use big results
        self.maxDiff = None

        # data to test
        device_on = True
        actual_dummy_result = {"result": True}
        expected_dummy_result = {
            "text": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. \
                Aenean commodo ligula eget dolor. Aenean massa. Cum sociis \
                natoque penatibus et magnis dis parturient montes, nascetur \
                ridiculus mus.",
        }

        # check that it works with multiple tables
        self.step_report.current_table = "First table"

        self.assertEqual(
            expected_dummy_result, expected_dummy_result, msg="Check my device is ready"
        )

        self.step_report.current_table = "Second table"

        with self.subTest("Non critical checks"):
            # This check will fail but the test continues
            self.assertFalse(device_on, msg="Some check")

        # assert with custom message
        # assert msg overwritten when step_report_message not null
        self.step_report.message = "Big data message"

        self.assertEqual(
            expected_dummy_result, expected_dummy_result, msg="Check big data"
        )

        self.assertEqual(
            expected_dummy_result, actual_dummy_result, msg="Check big data"
        )

        logging.info(f"I HAVE RUN 0.1.1 for tag {self.tag}!")
