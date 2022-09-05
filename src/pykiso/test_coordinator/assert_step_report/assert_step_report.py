##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Create a Step report
********************

:module: assert_step_report

:synopsis: Provide a detailed test view containing:
    - test name
    - test description
    - date of execution + elapsed time
    - information gathered during test
    - assertion detail: data_in, variable
        name of the data_in, expected, message

.. currentmodule:: assert_step_report

"""
import functools
import inspect
import logging
import re
import types
import typing
import unittest
from collections import OrderedDict, namedtuple
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Union

import jinja2

from pykiso.test_coordinator.test_result import BannerTestResult, TestCase
from pykiso.test_coordinator.test_xml_result import TestInfo, XmlTestResult

log = logging.getLogger(__name__)


# Global variables
# Store the Result Step report
ALL_STEP_REPORT = OrderedDict()
# Step result keys used by Jinja for columns name
REPORT_KEYS = ["message", "var_name", "expected_result", "actual_result", "succeed"]
# Parent method being reported ; Ignore sub call (assert in an assert)
_FUNCTION_TO_APPLY = r"|".join(["test", "run", "setup", "teardown"])

# Jinja template location
SCRIPT_PATH = str(Path(__file__).resolve().parent)

REPORT_TEMPLATE = "report_template.html.j2"


@dataclass
class StepReportData:
    # Store additional data fetched during test for
    # the step-report (even if not activated)
    header: dict = field(default_factory=dict)
    # Message for step in report
    message: str = ""
    # Test succeed flag
    # Set to false if one or more steps fail
    success: bool = True
    # Error message on step fail
    last_error_message: str = ""
    # Flag used for stopping interruptions on first fail for reporting
    continue_on_error: bool = False  # or use the failfast value?
    # Current report table
    current_table: typing.Optional[str] = None


def _get_variable_name(f_back: types.FrameType, assert_name: str) -> str:
    """Get the input parameter name to the assert method.

    According to unittest.TestCase, it is always placed first.
    That function read the source code as a text to find it.

    :param f_back: frame calling the assert method
    :param: assert_name: current assert method name

    return: variable name
    """
    expected_varname = ""
    # Get source code lines
    file = inspect.getsourcefile(f_back)
    lines = inspect.linecache.getlines(file)

    # Get current line number
    line_no = f_back.f_lineno

    # Get line content, if statement not
    # complete, read from bottom to up
    line = ""
    while assert_name not in line:
        # line_no start from 1 but list from 0
        line_no -= 1
        line = lines[line_no] + line

    # remove line break and spaces
    line = line.replace("\n", "")
    line = line.replace(" ", "")

    # remove current assert function name
    line = re.split(rf".*{assert_name}\(", line)[1]

    # Check the variable start names
    if re.findall(r"^[a-zA-Z]", line):
        # Get variable name
        expected_varname = re.findall(r"[a-zA-Z0-9_]+", line)[0]

    return expected_varname


def _get_expected(func_name: str, arguments: dict) -> str:
    """Get the assertion purpose and the expected value

    :param func_name: name of the assertion function
    :param arguments: argument of the function
        eg: {arg_name: value}

    :return: expected value
    """
    # Get assertion purpose (eg: get Equal from assertEqual)
    name = re.findall(r"([A-Z][a-z]+)", func_name)
    expected = " ".join(name)

    # Get expected value and parameters if exist
    # eg: assertAlmostEqual(50, 60, msg="message", delta=10)
    # but assertTrue(var1, "message") -> nothing else to do
    if len(arguments) >= 3:
        # Parameters not known in advance.
        # Remove the "input value" and the "msg".
        arguments_keys = list(arguments.keys())
        args = arguments.copy()
        args.pop("msg", None)
        # "input value" always 1st position
        args.pop(arguments_keys[0], None)
        # "expected value" always 2nd position
        expected_val = args.pop(arguments_keys[1], None)
        # Add expected value to string
        expected += f" to {expected_val}"
        # Add the additional parameter if exist
        if args:
            # only param are left in args
            expected += "; with"
            for key, value in args.items():
                expected += f" {key}={value},"
            # remove the coma from last loop
            expected = expected[:-1]

    return expected


def _prepare_report(test: unittest.case.TestCase, test_name: str) -> None:
    """Make ALL_STEP_REPORT variable ready for update

    Create the tree if required, otherwise, does nothing
    - CurrentTestClass
        - header: additional data
        - description: test description from test_run
        - file_path: test file location
        - time_result: start/end/elapsed time
        - test_list: store the steps result
            - test_name: list of steps

    :param test: test to be reported
    :param test_name: name of the function being tested
    """
    global ALL_STEP_REPORT

    test_class_name = type(test).__name__

    # Create the testClass
    if not ALL_STEP_REPORT.get(test_class_name):
        ALL_STEP_REPORT[test_class_name] = OrderedDict()
        # Add test succeed flag
        ALL_STEP_REPORT[test_class_name]["succeed"] = True
        # Add header (mutable object -> dictionary fed during test)
        ALL_STEP_REPORT[test_class_name]["header"] = test.step_report.header
        # Add description of the test -> Always test_run
        ALL_STEP_REPORT[test_class_name]["description"] = (
            test._testMethodDoc or "Not provided"
        )
        # Add test file path
        ALL_STEP_REPORT[test_class_name]["file_path"] = inspect.getfile(type(test))
        # Store the result (start, stop, elapsed time)
        ALL_STEP_REPORT[test_class_name]["time_result"] = OrderedDict()
        ALL_STEP_REPORT[test_class_name]["time_result"][
            "Start Time"
        ] = '"--junit" required'
        # Store the tests list
        ALL_STEP_REPORT[test_class_name]["test_list"] = OrderedDict()

    # Create the current test step storage
    if not ALL_STEP_REPORT[test_class_name]["test_list"].get(test_name):
        ALL_STEP_REPORT[test_class_name]["test_list"][test_name] = []


def _add_step(
    test_class_name: str,
    test_name: str,
    message: str,
    var_name: str,
    expected: typing.Any,
    received: any,
):
    global ALL_STEP_REPORT, REPORT_KEYS

    ALL_STEP_REPORT[test_class_name]["test_list"][test_name].append(
        dict(zip(REPORT_KEYS, [message, var_name, expected, received, True]))
    )


def assert_decorator(func):
    """Decorator to gather assertion information

    - MyTestClass
        - header: additional data
        - description: test purpose
        - file_path: test location
        - time_result: start/end/elapsed time
        - test_list: store the steps result
            - setUp : list of assert
            - test_run: list of assert

    .. note:: header is based on the variable ``step_report_header`` and
        description is based on the docstring of the test_run method

    .. code:: python

        MyTest(pykiso.BasicTest):
            def test_run(self):
                '''Here is my test description'''
                self.step_report.header["Voltage"] = 5

    :param func: function to decorate (expected assert method)

    return: The func output if it exists. Otherwise, None
    """

    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        """Decorator Main
        Fetch the assert step: message, var_name, expected, received

        return: The assertion method output if it exists. Otherwise, None
        """
        global _FUNCTION_TO_APPLY
        try:
            # Context
            currentframe = inspect.currentframe()
            f_back = currentframe.f_back
            test_name = f_back.f_code.co_name
            test_class = func.__self__
            test_class_name = type(test_class).__name__
            assert_name = func.__name__

            # filter parent call, only known function recorded
            parent_method = re.findall(_FUNCTION_TO_APPLY, test_name.lower())
            if parent_method:
                # Assign variables to signature
                signature = inspect.signature(func)
                arguments = signature.bind(*args, **kwargs).arguments
                test_name = test_class.step_report.current_table or test_name

                # 1. Gather message, var_name, expected, received
                # 1.1 Get message. default value: ""

                if test_class.step_report.message:
                    message = test_class.step_report.message
                    test_class.step_report.message = ""
                else:
                    message = arguments.get("msg", "")

                # ensure message is always present in the arguments
                # dictionary. (used in _get_expected)
                if not message and "msg" in signature.parameters:
                    arguments["msg"] = ""

                # 1.2. Get 'received" value (Always 1st argument)
                received = list(arguments.values())[0]

                # 1.3. Get variable name
                var_name = _get_variable_name(f_back, assert_name)

                # 1.4. Get Expected value
                expected = _get_expected(assert_name, arguments)

                # 2. Update report data
                # 2.1 Ensure report ready for update
                _prepare_report(test_class, test_name)

                # 2.2. Add new step
                _add_step(
                    test_class_name, test_name, message, var_name, expected, received
                )

        except Exception as e:
            log.error(f"Unable to update Step due to exception: {e}")

        # Run the assert method
        # When exception is thrown set test as failed and handle
        # the test assertion exception so that report doesn`t interrupt
        try:
            # if not test_class.step_report.continue_on_error and not test_class.step_report.success:
            #     raise Exception(test_class.step_report.last_error_message)
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"Assert step exception: {e}")
            test_class.step_report.last_error_message = f"{e}"
            if parent_method:
                ALL_STEP_REPORT[test_class_name]["test_list"][test_name][-1][
                    "succeed"
                ] = False
                ALL_STEP_REPORT[test_class_name]["succeed"] = False
            test_class.step_report.success = False
            if not test_class.step_report.continue_on_error:
                raise e

    return func_wrapper


def _parse_timestamp(timestamp: float) -> str:
    """Parse timestamp to date: alike 31/12/2021 23:59:59

    :param timestamp: Seconds since 01/01/1970

    :return: the date string
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%d/%m/%y %H:%M:%S")


def generate_step_report(
    test_result: Union[BannerTestResult, XmlTestResult],
    output_file: str,
) -> None:
    """Generate the HTML step report based on Jinja2 template

    :param test_result: Result of tests to generate the report from
    :param output_file: Report output file path
    """
    global ALL_STEP_REPORT, SCRIPT_PATH, REPORT_TEMPLATE

    succeeded_tests = test_result.successes + test_result.expectedFailures
    failed_test = (
        test_result.failures + test_result.errors + test_result.unexpectedSuccesses
    )

    # Update info for each test
    for test_case in succeeded_tests + failed_test:
        if isinstance(test_case, (TestCase, TestInfo)):
            # Case of success
            test_info = test_case
        elif isinstance(test_case, tuple) and isinstance(
            test_case[0], (TestCase, TestInfo)
        ):
            # Case of non success
            test_info = test_case[0]

        if isinstance(test_info, TestCase):
            class_name = test_info.__class__.__name__
            start_time = _parse_timestamp(test_info.start_time)
            stop_time = _parse_timestamp(test_info.stop_time)
        else:
            # test_info is TestInfo
            class_name = test_info.test_name.split(".")[-1]
            start_time = _parse_timestamp(test_info.test_result.start_time)
            stop_time = _parse_timestamp(test_info.test_result.stop_time)

        elapsed_time = test_info.elapsed_time

        # Update test_case
        if class_name in ALL_STEP_REPORT:
            ALL_STEP_REPORT[class_name]["time_result"]["Start Time"] = start_time
            ALL_STEP_REPORT[class_name]["time_result"]["End Time"] = stop_time
            ALL_STEP_REPORT[class_name]["time_result"]["Elapsed Time"] = round(
                elapsed_time, 2
            )

    # Render the source template
    render_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(SCRIPT_PATH))
    template = render_environment.get_template(REPORT_TEMPLATE)
    output_text = template.render({"ALL_STEP_REPORT": ALL_STEP_REPORT})

    output_file = Path(output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    # Write the output into the output file
    with output_file.open("w") as report_file:
        report_file.write(output_text)
