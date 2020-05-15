"""
Test Suite
**********

:module: test_suite

:synopsis: Create a generic test-suite based on the connected modules

.. currentmodule:: generic_test_suite

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

"""

import logging
import unittest
from collections.abc import Iterable
from operator import attrgetter

from . import message


class BaseTestSuite(unittest.TestCase):

    def __init__(self, test_suite_id: int, test_case_id: int, aux_list, args, kwargs):
        """ Initialize generic test-case """
        # Initialize base class
        super(BaseTestSuite, self).__init__(*args, **kwargs)
        # Save test information
        self.test_auxiliary_list = aux_list or []
        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id

    def cleanup_and_skip(self, info_to_print: str):
        """ Cleanup

        :param info_to_print: A message you want to print while cleaning up the test
        :type info_to_print: str
        """

        # Send aborts to all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.abort_command()
            aux.unlock_it()

        # Log error message
        logging.fatal(info_to_print)
        # Skip test
        self.skipTest(info_to_print)

    def base_function(self, step_name, test_command):
        """Base function used for test suite setup and teardown

        :param step_name: name of the current step
        :param test_command: A message you want to print while cleaning up the test
        """
        logging.info(
            "--------------- {}: {} ---------------".format(
                step_name, self.test_suite_id
            )
        )

        # Prepare message to send
        testcase_setup_message = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=test_command,
            test_suite=self.test_suite_id,
            test_case=0,
        )

        # Lock all auxiliaries
        for aux in self.test_auxiliary_list:
            locked = aux.lock_it(1)
            if locked is False:
                self.cleanup_and_skip("{} could not be locked!".format(aux))
        # Send the message to all auxiliaries
        for aux in self.test_auxiliary_list:
            if (
                aux.run_command(testcase_setup_message,
                                blocking=True, timeout_in_s=10)
                is not True
            ):
                self.cleanup_and_skip("{} could not be setup!".format(aux))
        # Unlock all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.unlock_it()


class BasicTestSuiteSetup(BaseTestSuite):

    def __init__(self, test_suite_id: int, test_case_id: int, aux_list, args, kwargs):
        """ Initialize generic test-case """
        # Initialize base class
        super(BasicTestSuiteSetup, self).__init__(
            test_suite_id, test_case_id, aux_list, args, kwargs)

    def test_suite_setUp(self):
        self.base_function(
            "SUITE SETUP", message.MessageCommandType.TEST_SUITE_SETUP)


class BasicTestSuiteTeardown(BaseTestSuite):

    def __init__(self, test_suite_id: int, test_case_id: int, aux_list, args, kwargs):
        """ Initialize generic test-case """
        # Initialize base class
        super(BasicTestSuiteTeardown, self).__init__(
            test_suite_id, test_case_id, aux_list, args, kwargs)

    def test_suite_tearDown(self):
        self.base_function(
            "SUITE TEARDOWN", message.MessageCommandType.TEST_SUITE_TEARDOWN)


class BasicTestSuite(unittest.TestSuite):
    """ Inherit from the unittest framework test-suite but build it for our integration tests """

    def __init__(
        self,
        modules_to_add_dir: str,
        test_filter_pattern: str,
        test_suite_id: int,
        args,
        kwargs,
    ):
        """ Initialize our custom unittest-test-suite

        .. note:
            1. Will Load from the given path the integration test modules under test
            2. Sort the given test case list by test suite/case id
            3. Place Test suite setup and teardown respectively at top and bottom of test case list
            4. Add sorted test case list to test suite
        """
        # Mother class initialization
        super(BasicTestSuite, self).__init__(*args, **kwargs)

        # load test from the specified folder
        loader = unittest.TestLoader()
        found_modules = loader.discover(
            modules_to_add_dir, pattern=test_filter_pattern)

        # sort the test case list by ascendant using test suite and test case id
        test_case_list = sorted(flatten(found_modules), key=attrgetter(
            'test_suite_id', 'test_case_id'))

        # get test suite fixture form current test_case_list
        fix_info = get_suite_fixture(test_case_list, (BasicTestSuiteSetup,
                                                      BasicTestSuiteTeardown))
        # based on test suite fixture found insert it
        for idx, fix in fix_info:
            test_case_list.pop(idx)
            if isinstance(fix, BasicTestSuiteSetup):
                test_case_list.insert(0, fix)
            else:
                test_case_list.append(fix)

        # add sorted test case list to test suite
        self.addTests(test_case_list)


def get_suite_fixture(tc_list, fix_type):
    """Retrieve test suite teardown and setup  

    :param tc_list: list of unittest.TestCase
    :param fix_type: type of fixture to search (setup/teardown)

    :return: tuple containing setup/teardown test list position,
    unittest.TestCase object, unittest.TestCase id
    """
    return [(idx, tc) for idx, tc in enumerate(tc_list) if isinstance(tc, fix_type)]


def flatten(it):
    """"Flatten all level of nesting"

    :param it: nested iterable

    :return: first not nested items
    """
    for x in it:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x
