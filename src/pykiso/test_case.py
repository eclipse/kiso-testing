"""
Generic Test
**************************

:module: test_case

:synopsis: Baisc extensible implementation of a TestCase.

.. currentmodule:: test_case

:Copyright: Copyright (c) 2010-2020 Robert Bosch GmbH
    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.

    SPDX-License-Identifier: EPL-2.0

.. note:: TODO later on will inherit from a metaclass to get the id parameters
"""

from typing import List, Dict
from pykiso import AuxiliaryInterface

import logging
import unittest
import timeout_decorator
import functools

# Import based on the caller
import sys

# Import the framework modules
from . import message


class BasicTest(unittest.TestCase):
    """ Base for test-cases """

    def __init__(
        self,
        test_suite_id: int = 0,
        test_case_id: int = 0,
        aux_list: List[AuxiliaryInterface] = None,
        args: List = None,
        kwargs: Dict = None,
    ):
        """ Initialize generic test-case """
        # Initialize base class
        super(BasicTest, self).__init__(*args, **kwargs)
        # Save list of test auxiliaries to use (already initialize)
        self.test_auxiliary_list = aux_list or []
        # Save test information
        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id

    def cleanup_and_skip(self, info_to_print: str):
        """ Cleanup what was created in the Test-case

        :param info_to_print: A message you want to print while cleaning up the test
        :type info_to_print: str
        """
        # Send aborts to all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.abort_command()
        # Unlock all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.unlock_it()
        # Log error message
        logging.fatal(info_to_print)
        # Skip test
        self.skipTest(info_to_print)

    def evaluate_message(
        self, aux: AuxiliaryInterface, reported_message: message.Message
    ) -> bool:
        """ Evaluate the report content

        :param aux: Auxiliary that sent the answer (Just for log perpose)

        :param reported_message: received message to evaluate

        :return: True - Report received (does not mean it was successfull) / False - Report not received
        """
        return_value = False
        if reported_message is not None:
            # Verify message content
            if reported_message.get_message_type() == message.MessageType.LOG:
                # It is a log message
                logging.info(reported_message)
            elif reported_message.get_message_type() == message.MessageType.REPORT:
                # If the report is a fail, log and abort the test
                if (
                    reported_message.get_message_sub_type()
                    == message.MessageReportType.TEST_FAILED
                ):
                    self.cleanup_and_skip(
                        "Test running on {} failed with {}".format(
                            aux, reported_message
                        )
                    )
                # If success, return
                return_value = True
            else:
                # Unexpected message received
                logging.info(
                    "Unexpected message received: {}".format(reported_message))
        return return_value

    def setUp(self):
        logging.info(
            "--------------- SETUP: {}, {} ---------------".format(
                self.test_suite_id, self.test_case_id
            )
        )
        # Prepare message to send
        testcase_setup_message = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=message.MessageCommandType.TEST_CASE_SETUP,
            test_suite=self.test_suite_id,
            test_case=self.test_case_id,
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

    # @timeout_decorator.timeout(5) # Timeout of 10 second as generic test-case # TODO: Only working on linux
    def test_run(self):
        logging.info(
            "--------------- RUN: {}, {} ---------------".format(
                self.test_suite_id, self.test_case_id
            )
        )
        # Prepare message to send
        testcase_run_message = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=message.MessageCommandType.TEST_CASE_RUN,
            test_suite=self.test_suite_id,
            test_case=self.test_case_id,
        )
        # Send test start through all auxiliaries
        for aux in self.test_auxiliary_list:
            if (
                aux.run_command(testcase_run_message,
                                blocking=True, timeout_in_s=10)
                is not True
            ):
                self.cleanup_and_skip("{} could not be run!".format(aux))
        # Loop until all messages are recieved
        list_of_aux_with_received_reports = [
            False] * len(self.test_auxiliary_list)
        while False in list_of_aux_with_received_reports:
            # Loop through all auxiliaries
            for i, aux in enumerate(self.test_auxiliary_list):
                if list_of_aux_with_received_reports[i] == False:
                    # Wait for a report
                    reported_message = aux.wait_and_get_report()
                    # Check the received message
                    list_of_aux_with_received_reports[i] = self.evaluate_message(
                        aux, reported_message
                    )

    def tearDown(self):
        logging.info(
            "--------------- TEARDOWN: {}, {} ---------------".format(
                self.test_suite_id, self.test_case_id
            )
        )
        # Prepare message to send
        testcase_setup_message = message.Message(
            msg_type=message.MessageType.COMMAND,
            sub_type=message.MessageCommandType.TEST_CASE_TEARDOWN,
            test_suite=self.test_suite_id,
            test_case=self.test_case_id,
        )
        # Send the message to all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.run_command(testcase_setup_message,
                            blocking=True, timeout_in_s=1)
        # Unlock all auxiliaries
        for aux in self.test_auxiliary_list:
            aux.unlock_it()


def define_test_parameters(
    suite_id: int = 0,
    case_id: int = 0,
    aux_list: List[AuxiliaryInterface] = None,
):
    """ Decorator to fill out test parameters of the BasicTest automatically. """
    def generate_modified_class(DecoratedClass):
        """ Generates the same class but with the test IDs already filled.
        It works as a partially filled-out call to the __init__ method.
        """

        class NewClass(DecoratedClass):
            """Modified {DecoratedClass.__name__}, with the __init__ method
            already filled out with the following test-parameters:

            Suite ID:    {suite_id}
            Case ID:     {case_id}
            Auxiliaries: {auxes}"""

            @functools.wraps(DecoratedClass.__init__)
            def __init__(self, *args, **kwargs):
                super(NewClass, self).__init__(
                    suite_id, case_id, aux_list, args, kwargs,
                )

        NewClass.__doc__ = NewClass.__doc__.format(
            DecoratedClass=DecoratedClass,
            suite_id=suite_id,
            case_id=case_id,
            auxes=[aux.__class__.__name__ for aux in aux_list or []],
        )

        return NewClass

    return generate_modified_class
