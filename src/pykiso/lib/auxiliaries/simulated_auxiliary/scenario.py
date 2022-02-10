##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Scenario
********

:module: scenario

:synopsis: base object used to create pre-defined virtual DUT scenario.

.. currentmodule:: scenario

.. warning:: Still under test
"""

from collections import UserList

from .response_templates import ResponseTemplates


class Scenario(UserList):
    """Container used to create pre-defined virtual DUT scenario."""

    pass


class TestScenario:
    """Encapsulate all possible test's scenarios."""

    @classmethod
    def handle_successful(cls) -> Scenario:
        """Return a scenario to handle a complete successful
        test case exchange(TEST CASE setup->run->teardown).

        :return: Scenario instance containing all steps
        """
        return Scenario(
            [
                ResponseTemplates.ack_with_report_ok,
                ResponseTemplates.ack_with_report_ok,
                ResponseTemplates.ack_with_report_ok,
            ]
        )

    @classmethod
    def handle_communication_lost(cls) -> Scenario:
        return Scenario([ResponseTemplates.ack])

    class VirtualTestCase:
        """Used to gather all virtual DUT test case scenarios based on
        their fixture level (setup, run, teardown).
        """

        class Setup:
            """Used to gather all possible scenarios linked to a test
            case setup execution.
            """

            @classmethod
            def handle_failed_report_setup(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with failed report at setup phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_nok,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_not_implemented_report_setup(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with not implemented report at setup phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_not_implemented,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_setup_ack(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during ACK to setup Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        None,
                        None,
                        ResponseTemplates.ack,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_setup_report(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during report to setup Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack,
                        None,
                        None,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

        class Run:
            """Used to gather all possible scenarios linked to a test case
            run execution.
            """

            @classmethod
            def handle_failed_report_run(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with failed report at run phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_nok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_successful_report_run_with_log(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with successful log and report at run phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_logs_and_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_failed_report_run_with_log(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with failed log and report at run phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_logs_and_report_nok,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_not_implemented_report_run(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with not implemented report at run phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_not_implemented,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_run_ack(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during ACK to run Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        None,
                        None,
                        ResponseTemplates.ack,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_run_report(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during report to run Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack,
                        None,
                        None,
                        ResponseTemplates.ack_with_report_ok,
                    ]
                )

        class Teardown:
            """Used to gather all possible scenarios linked to a test case
            teardown execution.
            """

            @classmethod
            def handle_failed_report_teardown(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with failed report at teardown phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_nok,
                    ]
                )

            @classmethod
            def handle_not_implemented_report_teardown(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with not implemented report at teardown phase.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_not_implemented,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_teardown_ack(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during ACK to teardown Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                        None,
                        None,
                        ResponseTemplates.ack,
                    ]
                )

            @classmethod
            def handle_lost_communication_during_teardown_report(cls) -> Scenario:
                """Return a scenario to handle a complete test case
                with lost of communication during report to teardown Command.

                :return: Scenario instance containing all steps
                """
                return Scenario(
                    [
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack_with_report_ok,
                        ResponseTemplates.ack,
                        None,
                        None,
                    ]
                )

    class VirtualTestSuite:
        """Used to gather all virtual DUT test suite scenarios based on
        their fixture level (setup, teardown).
        """

        class Setup:
            """Used to gather all possible scenarios linked to a test suite
            setup execution.
            """

            @classmethod
            def handle_failed_report_setup(cls) -> Scenario:
                """Return a scenario to handle a test suite setup
                with report failed.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack_with_report_nok])

            @classmethod
            def handle_not_implemented_report_setup(cls) -> Scenario:
                """Return a scenario to handle a test suite setup
                with report not implemented.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack_with_report_not_implemented])

            @classmethod
            def handle_lost_communication_during_setup_ack(cls) -> Scenario:
                """Return a scenario to handle a lost of communication
                during ACK to setup command.

                :return: Scenario instance containing all steps
                """
                return Scenario([None, None, ResponseTemplates.ack])

            @classmethod
            def handle_lost_communication_during_setup_report(cls) -> Scenario:
                """Return a scenario to handle a lost of communication
                during report to setup command.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack, None, None])

        class Teardown:
            """Used to gather all possible scenarios linked to a test suite
            teardown execution.
            """

            @classmethod
            def handle_failed_report_teardown(cls) -> Scenario:
                """Return a scenario to handle a test suite teardown
                with report failed.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack_with_report_nok])

            @classmethod
            def handle_not_implemented_report_teardown(cls) -> Scenario:
                """Return a scenario to handle a test suite teardown
                with report not implemented.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack_with_report_not_implemented])

            @classmethod
            def handle_lost_communication_during_teardown_ack(cls) -> Scenario:
                """Return a scenario to handle a lost of communication
                during ACK to teardown command.

                :return: Scenario instance containing all steps
                """
                return Scenario([None, None, ResponseTemplates.ack])

            @classmethod
            def handle_lost_communication_during_teardown_report(cls) -> Scenario:
                """Return a scenario to handle a lost of communication
                during report to teardown command.

                :return: Scenario instance containing all steps
                """
                return Scenario([ResponseTemplates.ack, None, None])
