import pykiso
import logging

from pykiso.auxiliaries import aux1, aux2


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
class SuiteSetup(pykiso.BasicTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=1, aux_list=[aux1, aux2])
class SuiteTearDown(pykiso.BasicTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[aux1])
class MyTest(pykiso.BasicTest):
    def test_run(self):
        logging.info("I HAVE RUN 0.1.1!")


@pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=[aux2])
class MyTest2(pykiso.BasicTest):
    def test_run(self):
        logging.info("I HAVE RUN 0.1.2!")


@pykiso.define_test_parameters(suite_id=1, case_id=3, aux_list=[aux1])
class MyTest3(pykiso.BasicTest):
    def test_run(self):
        logging.info("I HAVE RUN 0.1.3!")
