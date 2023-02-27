##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
:module: exceptions

:synopsis: Define all custom exceptions raised by pykiso framework

.. currentmodule:: exceptions
"""


class PykisoError(Exception):
    """Pykiso specific exception used as basis for all others."""

    def __str__(self):
        return self.message


class TestCollectionError(PykisoError):
    """Collection of test cases by the TestLoader failed."""

    def __init__(self, test_suite_dir: str) -> None:
        """Initialize attributes.

        :param test_suite_dir: path to the test suite in which a test
            case failed to be loaded.
        """
        self.message = f"Failed to collect test suite '{test_suite_dir}'"
        super().__init__(self.message)


class AuxiliaryCreationError(PykisoError):
    """Raised when an auxiliary instance creation failed."""

    def __init__(self, aux_name: str) -> None:
        """Initialize attributes.

        :param aux_name: configured auxiliary alias.
        """
        self.message = f"Auxiliary {aux_name} failed at instance creation"
        super().__init__(self.message)


class ConnectorRequiredError(PykisoError):
    """Raised when an auxiliary instance creation failed because a connector is
    required and none is provided
    """

    def __init__(self, aux_name: str) -> None:
        """Initialize attributes.

        :param aux_name: configured auxiliary alias.
        """
        self.message = f"A connector is required for {aux_name} and none is provided"
        super().__init__(self.message)


class InvalidTestModuleName(PykisoError):
    """Raised when a invalid python module name is covered by test file pattern
    of either the cli or the yaml config
    """

    def __init__(self, name: str) -> None:
        self.message = (
            f"Test files need to be valid python module names but '{name}' is invalid"
            "\nModule name can only contain letters, numbers, _ (underscore), "
            "needs to start with a letter or underscore"
        )
        super().__init__(self.message)
