import pykiso

from pykiso.auxiliaries import aux1, aux2


@pykiso.define_test_parameters(suite_id=2, case_id=0, aux_list=[aux1, aux2])
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=2, case_id=0, aux_list=[aux1, aux2])
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=2, case_id=1, aux_list=[aux1])
class MyTest(pykiso.BasicTest):
    pass


@pykiso.define_test_parameters(suite_id=2, case_id=2, aux_list=[aux2])
class MyTest2(pykiso.BasicTest):
    pass
