import pytest
from _pytest.pytester import HookRecorder, Pytester

import pykiso


@pytest.fixture
def dummy_pykiso_testsuite(pytester: Pytester):
    pytester.makefile(ext=".yaml", dummy_pykiso=pytest.DUMMY_YAML)
    pytester.makepyfile(test_suite=pytest.DUMMY_PYKISO_TESTSUITE)
    # pytester.make_hook_recorder(pytest.PytestPluginManager)


@pytest.mark.slow
def test_pykiso_testsuite(pytester: Pytester, dummy_pykiso_testsuite):
    # pytest has to be run within a subprocess to properly uninitialize pykiso's import magic
    result = pytester.runpytest_subprocess(
        "./dummy_pykiso.yaml", "--log-cli-level", "INFO"
    )

    result.assert_outcomes(passed=4)


@pytest.mark.slow
def test_pykiso_testsuite_with_tags(pytester: Pytester, dummy_pykiso_testsuite):
    result = pytester.runpytest_subprocess(
        "./dummy_pykiso.yaml", "--tags", "variant=var1", "--log-cli-level", "INFO"
    )

    result.assert_outcomes(passed=2, skipped=2)
