import pytest
import unittest
import subprocess
import time
from pykiso.dynamic_loader import DynamicImportLinker
from pykiso import CChannel
from pykiso import Flasher

from pykiso import test_case
from pykiso import test_suite
from pykiso.lib.connectors import cc_example
from pykiso.lib.auxiliaries import example_test_auxiliary
from pykiso.test_case import define_test_parameters


EX_MODULE = """
class TestConnector:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class TestAux:
    def __init__(self, com, *args, **kwargs):
        self.com = com
        self.args = args
        self.kwargs = kwargs
        self.is_instance = False
    def create_instance(self):
        self.is_instance = True
    def stop(self):
        self.is_instance = False
"""


@pytest.fixture(scope="module")
def example_module(tmp_path_factory):
    """
    create a "test_module.py" at a temporary directory
    """
    tmp_path = tmp_path_factory.getbasetemp()
    mod_path = tmp_path / "test_module.py"
    with open(mod_path, "w") as f:
        f.write(EX_MODULE)
    return mod_path


@pytest.fixture
def tmp_file(tmp_path):
    f = tmp_path / "test.bin"
    f.write_text("")

    return f


@pytest.fixture
def cchannel_inst(mocker):
    class TCChan(CChannel):
        def __init__(self, *args, **kwargs):
            super(TCChan, self).__init__(*args, **kwargs)

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")

    return TCChan(name="test-channel")


@pytest.fixture
def flasher_inst(tmp_file, mocker):
    class TFlash(Flasher):
        def __init__(self, *args, **kwargs):
            super(TFlash, self).__init__(*args, **kwargs)

        open = mocker.stub(name="open")
        close = mocker.stub(name="close")
        flash = mocker.stub(name="flash")

    return TFlash(name="test-flash", binary=tmp_file)


@pytest.fixture
def serial_interface(tmp_path):
    BAUD = 9600

    uart0 = str(tmp_path / "vt0")
    uart1 = str(tmp_path / "vt1")

    print("running 'socat -d -d pty,link=~/vt0,rawer pty,link=~/vt1,rawer'")
    socat = subprocess.Popen(
        [
            "/usr/bin/env",
            "socat",
            "-d",
            "-d",
            f"pty,link={uart0},rawer",
            f"pty,link={uart1},rawer",
        ],
    )
    time.sleep(0.1)  # wait for socat to be up and running
    if socat.returncode is not None:
        raise RuntimeError("error running socat, check your system.")
    yield (uart0, uart1)
    socat.terminate()


@pytest.fixture(scope="class")
def CustomTestCaseAndSuite(request):
    
    class InitTestCaseAndSuite:

        def __init__(self):
            self.channel_in_use = cc_example.CCExample
            self.auxiliary_in_use = example_test_auxiliary.ExampleAuxiliary
            self.connectors = []
            self.auxiliaries = []
            self.suite = unittest.TestSuite()
            self.custom_test_suite = None

        def create_communication_pipeline(self, max_com):
            for _ in range(max_com):
                self.connectors.append(self.channel_in_use())
                self.auxiliaries.append(self.auxiliary_in_use(com=self.connectors[-1]))
                self.auxiliaries[-1].create_instance()

        def prepare_default_test_cases(self, param):
            @define_test_parameters(suite_id=param[0], case_id=param[1], aux_list=param[2])
            class MyTestCase(test_case.BasicTest):
                pass

            self.suite.addTest(MyTestCase("test_run"))

        def prepare_default_test_suites(self, test_suite_params):

            class MyTestSuite(test_suite.BasicTestSuite):
                def __init__(self, params):
                    super(MyTestSuite, self).__init__(*params)

            # Start integration test
            self.custom_test_suite = MyTestSuite(test_suite_params)

        def stop(self):
            for aux in self.auxiliaries :
                aux.delete_instance()
                aux.stop()

    request.cls.init = InitTestCaseAndSuite()