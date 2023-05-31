##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

from textwrap import dedent

import pytest
from _pytest.pytester import Pytester


@pytest.fixture
def dummy_yaml():
    """Create a pykiso config file."""
    return dedent(
        """
        auxiliaries:
          aux1:
            connectors:
              com: chan1
            config: null
            type: pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary
          aux2:
            connectors:
              com: chan2
            type: pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary
        connectors:
          chan1:
            config: null
            type: pykiso.lib.connectors.cc_example:CCExample
          chan2:
            type: pykiso.lib.connectors.cc_example:CCExample
        test_suite_list:
        - suite_dir: ./
          test_filter_pattern: '*.py'
          test_suite_id: 1
        """
    )


@pytest.fixture
def dummy_pykiso_testmodule():
    """Factory fixture to create a pykiso test module."""

    def _make(add_failure: bool = False, add_error: bool = False):
        return dedent(
            f"""
            import pykiso
            from pykiso.auxiliaries import aux1, aux2

            @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
            class SuiteSetup(pykiso.BasicTestSuiteSetup):
                def test_suite_setUp(self):
                    pass

            @pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
            class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
                def test_suite_tearDown(self):
                    pass

            @pykiso.define_test_parameters(
                suite_id=1, case_id=1, aux_list=[aux1], test_ids={{"id": ["Req1", "Req2"]}}, tag={{"variant": ["variant1"]}}
            )
            class MyTest1(pykiso.BasicTest):

                def setUp(self):
                    self.side_effect = iter([False, True])

                @pykiso.retry_test_case(max_try=2, rerun_setup=False, rerun_teardown=False)
                def test_run1(self):
                    {'raise RuntimeError' if add_error else ''}
                    self.assertTrue(next(self.side_effect))
                    self.assertTrue(aux1.is_instance)

                def tearDown(self):
                    super().tearDown()

            @pykiso.define_test_parameters(
                suite_id=1, case_id=2, aux_list=[aux2], tag={{"branch_level": ["nightly"]}}
            )
            class MyTest2(pykiso.BasicTest):
                def test_run(self):
                    self.assertTrue({False if add_failure else True})
            """
        )

    return _make


@pytest.fixture
def dummy_pytest_testmodule():
    """Factory fixture to create a pytest test module with pykiso features."""

    def _make(add_failure: bool = False, add_error: bool = False):
        return dedent(
            f"""
            import pytest

            @pytest.mark.tags(variant=["var1"])
            def test_mytest1(aux1):
                assert aux1.is_instance == {False if add_failure else True}

            @pytest.mark.tags(variant="var2")
            def test_mytest2(aux2):
                {'raise RuntimeError' if add_error else ''}
                assert aux2.start() == True
            """
        )

    return _make


@pytest.fixture
def dummy_pykiso_testsuite(pytester: Pytester, dummy_yaml, dummy_pykiso_testmodule):
    """
    Fixture to create a pykiso test suite, i.e. a pykiso config file in YAML
    format named 'dummy_config.yaml' and a test module named 'test_suite.py'
    invoked by the config file.
    """
    config_path = pytester.makefile(ext=".yaml", dummy_config=dummy_yaml)
    pytester.makepyfile(test_suite=dummy_pykiso_testmodule())
    return config_path


@pytest.fixture
def dummy_pytest_testsuite(pytester: Pytester, dummy_yaml, dummy_pytest_testmodule):
    """
    Fixture to create a pykiso test suite in pytest style, i.e. a pykiso
    config file in YAML format named 'dummy_config.yaml' and a test module
    named 'test_suite.py' invoked by the config file, containing pytest-style
    test cases.
    """
    config_path = pytester.makefile(ext=".yaml", dummy_config=dummy_yaml)
    pytester.makepyfile(test_suite=dummy_pytest_testmodule())
    return config_path


@pytest.fixture
def dummy_mixed_testsuite(
    pytester: Pytester, dummy_yaml, dummy_pykiso_testmodule, dummy_pytest_testmodule
):
    """
    Fixture to create a pykiso test suite containing a pykiso config file
    in YAML format named 'dummy_config.yaml' and a test module that mixes
    pykiso-style and pytest-style test cases.
    """
    config_path = pytester.makefile(ext=".yaml", dummy_config=dummy_yaml)
    pytester.makepyfile(
        test_suite=dummy_pytest_testmodule() + "\n" + dummy_pykiso_testmodule()
    )
    return config_path


@pytest.fixture
def dummy_multiple_testsuites(
    pytester: Pytester, dummy_yaml, dummy_pykiso_testmodule, dummy_pytest_testmodule
):
    """
    Fixture to create a pykiso test suite containing a pykiso config file
    in YAML format named 'dummy_config.yaml' and 2 test modules, one with
    pykiso-style test cases and the other with pytest-style.
    """
    config_path = pytester.makefile(ext=".yaml", dummy_config=dummy_yaml)
    pytester.makepyfile(test_suite=dummy_pytest_testmodule())
    pytester.makepyfile(test_suite2=dummy_pykiso_testmodule())
    return config_path
