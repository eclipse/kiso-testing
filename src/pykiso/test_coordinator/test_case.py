##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Generic Test
************

:module: test_case

:synopsis: Basic extensible implementation of a TestCase, and of a Remote
TestCase for Message Protocol / TestApp usage.

.. currentmodule:: test_case

.. note:: TODO later on will inherit from a metaclass to get the id parameters
"""
from __future__ import annotations

import functools
import logging
import unittest
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from .. import message
from ..interfaces.thread_auxiliary import AuxiliaryInterface
from ..logging_initializer import get_logging_options, initialize_logging
from .test_message_handler import test_app_interaction

if TYPE_CHECKING:
    from .test_suite import BaseTestSuite

log = logging.getLogger(__name__)


class BasicTest(unittest.TestCase):
    """Base for test-cases."""

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
        tag: Union[Dict[str, List[str]], None],
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize generic test-case.

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used auxiliaries
        :param setup_timeout: maximum time (in seconds) used to wait
            for a report during setup execution
        :param run_timeout: maximum time (in seconds) used to wait for
            a report during test_run execution
        :param teardown_timeout: the maximum time (in seconds) used to
            wait for a report during teardown execution
        :param test_ids: jama references to get the coverage
            eg: {"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}
        :param tag: dictionary allowing users to filter the tests based
            on the keys and their value.
        """
        # Initialize base class
        super().__init__(*args, **kwargs)
        # Save list of test auxiliaries to use (already initialize)
        self.test_auxiliary_list = aux_list or []
        # Save test information
        self.test_suite_id = test_suite_id
        self.test_case_id = test_case_id
        self.test_ids = test_ids
        self.tag = tag
        self.start_time = self.stop_time = self.elapsed_time = 0
        if any([setup_timeout, run_timeout, teardown_timeout]) and not isinstance(
            self, RemoteTest
        ):
            log.warning(
                "BasicTest does not support test timeouts, it will be discarded"
            )

    def cleanup_and_skip(self, aux: AuxiliaryInterface, info_to_print: str) -> None:
        """Cleanup auxiliary and log reasons.

        :param aux: corresponding auxiliary to abort
        :param info_to_print: A message you want to print while cleaning up the test
        """
        # Log error message
        log.critical(info_to_print)

        # Send aborts to corresponding auxiliary
        if aux.send_abort_command(timeout=10) is not True:
            log.critical(f"Error occurred during abort command on auxiliary {aux}")

        self.fail(info_to_print)

    @classmethod
    def setUpClass(cls) -> None:
        """A class method called before tests in an individual class are
        run.

        This implementation is only mandatory to enable logging in junit
        report. The logging configuration has to be call inside test
        runner run, otherwise stdout is never caught.
        """
        options = get_logging_options()
        if options.report_type == "junit":
            initialize_logging(
                None, options.log_level, options.verbose, options.report_type
            )

    def setUp(self) -> None:
        """Startup hook method to execute code before each test method."""
        pass

    def tearDown(self) -> None:
        """Closure hook method to execute code after each test method."""
        pass


class RemoteTest(BasicTest):
    """Base test-cases for Message Protocol / TestApp usage."""

    response_timeout: int = 10

    def __init__(
        self,
        test_suite_id: int,
        test_case_id: int,
        aux_list: Union[List[AuxiliaryInterface], None],
        setup_timeout: Union[int, None],
        run_timeout: Union[int, None],
        teardown_timeout: Union[int, None],
        test_ids: Union[dict, None],
        tag: Union[Dict[str, List[str]], None],
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize TestApp test-case.

        :param test_suite_id: test suite identification number
        :param test_case_id: test case identification number
        :param aux_list: list of used auxiliaries
        :param setup_timeout: maximum time (in seconds) used to wait
            for a report during setup execution
        :param run_timeout: maximum time (in seconds) used to wait for
            a report during test_run execution
        :param teardown_timeout: the maximum time (in seconds) used to
            wait for a report during teardown execution
        :param test_ids: jama references to get the coverage
            eg: {"Component1": ["Req1", "Req2"], "Component2": ["Req3"]}
        :param tag: dictionary containing lists of variants and/or test
            levels when only a subset of tests needs to be executed
        """
        super().__init__(
            test_suite_id,
            test_case_id,
            aux_list,
            setup_timeout,
            run_timeout,
            teardown_timeout,
            test_ids,
            tag,
            *args,
            **kwargs,
        )
        self.setup_timeout = setup_timeout or RemoteTest.response_timeout
        self.run_timeout = run_timeout or RemoteTest.response_timeout
        self.teardown_timeout = teardown_timeout or RemoteTest.response_timeout

    @test_app_interaction(
        message_type=message.MessageCommandType.TEST_CASE_SETUP, timeout_cmd=5
    )
    def setUp(self) -> None:
        """Startup hook method to execute code before each test method."""
        pass

    @test_app_interaction(
        message_type=message.MessageCommandType.TEST_CASE_RUN, timeout_cmd=5
    )
    def test_run(self) -> None:
        """Hook method from unittest in order to execute test case."""
        pass

    @test_app_interaction(
        message_type=message.MessageCommandType.TEST_CASE_TEARDOWN, timeout_cmd=5
    )
    def tearDown(self) -> None:
        """Closure hook method to execute code after each test method."""
        pass


def define_test_parameters(
    suite_id: int = 0,
    case_id: int = 0,
    aux_list: List[AuxiliaryInterface] = None,
    setup_timeout: Optional[int] = None,
    run_timeout: Optional[int] = None,
    teardown_timeout: Optional[int] = None,
    test_ids: Optional[dict] = None,
    tag: Optional[Dict[str, List[str]]] = None,
):
    """Decorator to fill out test parameters of the BasicTest and RemoteTest automatically."""

    def generate_modified_class(
        DecoratedClass: Type[Union[BasicTest, BaseTestSuite]]
    ) -> Type[Union[BasicTest, BaseTestSuite]]:
        """For basic test-case, generates the same class but with the test IDs
        already filled. It works as a partially filled-out call to the __init__ method.
        """

        class NewClass(DecoratedClass):
            """Modified {DecoratedClass.__name__}, with the __init__ method
            already filled out with the following test-parameters:
            Suite ID:    {suite_id}
            Case ID:     {case_id}
            Auxiliaries: {auxes}
            setup_timeout: {setup_timeout}
            run_timeout: {run_timeout}
            teardown_timeout: {teardown_timeout}
            test_ids: {test_ids}
            tag: {tag}
            """

            @functools.wraps(DecoratedClass.__init__)
            def __init__(self, *args, **kwargs):
                super(NewClass, self).__init__(
                    suite_id,
                    case_id,
                    aux_list,
                    setup_timeout,
                    run_timeout,
                    teardown_timeout,
                    test_ids,
                    tag,
                    *args,
                    **kwargs,
                )

        NewClass.__doc__ = NewClass.__doc__.format(
            DecoratedClass=DecoratedClass,
            suite_id=suite_id,
            case_id=case_id,
            auxes=[aux.__class__.__name__ for aux in aux_list or []],
            setup_timeout=setup_timeout,
            run_timeout=run_timeout,
            teardown_timeout=teardown_timeout,
            test_ids=test_ids,
            tag=tag,
        )

        # Used to display the current test module in the test result
        NewClass.__module__ = DecoratedClass.__module__
        # Passing the name of the decorated class to the new returned class
        # in order to get the test case name and references, i.e. suite_id and case_id
        # in the test results in the console and in the report.
        # Changing __name__ is necessary to make the test name appear in the test results in the console.
        # Changing __qualname__ is necessary to make the test name appear in the test results in the report.
        ids = "" if suite_id == 0 and case_id == 0 else f"-{suite_id}-{case_id}"
        NewClass.__name__ = f"{DecoratedClass.__name__}{ids}"
        NewClass.__qualname__ = f"{DecoratedClass.__qualname__}{ids}"
        return NewClass

    return generate_modified_class


def retry_test_case(
    max_try: int = 2,
    rerun_setup: bool = False,
    rerun_teardown: bool = False,
    stability_test: bool = False,
):
    """Decorator: retry mechanism for testCase.

    The aim is to cover the 2 following cases:

        - Unstable test : get the test pass within the {max_try} attempt

        - Stability test : run {max_try} time the test expecting no error

    The **retry_test_case** comes with the possibility to re-run the setUp and
    tearDown methods automatically.

    :param max_try: maximum number of try to get the test pass.
    :param rerun_setup: call the "setUp" method of the test.
    :param rerun_teardown: call the "tearDown" method of the test.
    :param stability_test: run {max_try} time the test and raise an exception if an error occurs.

    :return: None, a testCase is not supposed to return anything.
    :raise Exception: if stability_test, the exception that occurred during the execution; if
        not stability_test, the exception that occurred at the last try.
    """

    def decorator(func):
        @functools.wraps(func)
        def func_wrapper(self: BasicTest) -> None:
            # track the current execution for logging
            current_execution = None

            for retry_nb in range(1, max_try + 1):
                try:
                    # by the 2nd attempt, end the test with the teardown and start with setUp
                    if retry_nb > 1:
                        if rerun_teardown:
                            current_execution = self.tearDown
                            self.tearDown()
                        if rerun_setup:
                            current_execution = self.setUp
                            self.setUp()

                    # run the method (eg: test_run(self))
                    current_execution = func
                    func(self)
                    if not stability_test:
                        break
                    else:
                        # Clearly separate tests
                        log.info(
                            f">>>>>>>>>> Stability test {retry_nb}/{max_try} succeed <<<<<<<<<<"
                        )

                except Exception as e:
                    # log: test_name (class), method (setUp, test_run, tearDown) and the error.
                    log.warning(
                        f"{self.__class__.__name__}.{current_execution.__name__} failed with exception: {e}."
                    )

                    # raise the exception that occurred during the latest attempt
                    if retry_nb == max_try or stability_test:
                        log.error(
                            f">>>>>>>>>> Test {retry_nb}/{max_try} failed <<<<<<<<<<"
                        )
                        raise e

                    # print counter only after failing test to avoid spamming the console
                    log.info(f">>>>>>>>>> Attempt: {retry_nb +1}/{max_try} <<<<<<<<<<")

        return func_wrapper

    return decorator
