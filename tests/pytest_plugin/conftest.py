import pytest

pytest_plugins = ["pytester"]


pytest.DUMMY_YAML = """
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
  test_filter_pattern: 'test_suite.py'
  test_suite_id: 1
"""

pytest.DUMMY_PYKISO_TESTSUITE = """
import pykiso
from pykiso.auxiliaries import aux1, aux2

@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
class SuiteSetup(pykiso.RemoteTestSuiteSetup):
    def test_suite_setUp(self):
        pass


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
class SuiteTearDown(pykiso.RemoteTestSuiteTeardown):
    def test_suite_tearDown(self):
        pass


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=1,
    aux_list=[aux1],
    test_ids={"id": ["Req1", "Req2"]},
    tag={"variant": ["variant1"], "branch_level": ["daily"]},
)
class MyTest1(pykiso.BasicTest):

    @pykiso.retry_test_case(max_try=3)
    def setUp(self):
        self.side_effect = iter([False, True])

    @pykiso.retry_test_case(max_try=2, rerun_setup=False, rerun_teardown=False)
    def test_run(self):
        self.assertTrue(next(self.side_effect))
        self.assertTrue(aux1.is_instance)

    @pykiso.retry_test_case(max_try=3)
    def tearDown(self):
        super().tearDown()


@pykiso.define_test_parameters(
    suite_id=1,
    case_id=2,
    aux_list=[aux2],
    test_ids={"Component1": ["Req"]},
    tag={"branch_level": ["nightly"]},
)
class MyTest2(pykiso.RemoteTest):
    def test_run(self):
        self.assertTrue(True)
"""
