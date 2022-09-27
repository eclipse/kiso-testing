##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import itertools
import logging
import shutil
import subprocess
import time
import unittest
from unittest import TestResult

import pytest

from pykiso import CChannel, Flasher, cli, message, test_suite
from pykiso.lib.auxiliaries import dut_auxiliary
from pykiso.lib.connectors import cc_example
from pykiso.lib.connectors.cc_pcan_can import CCPCanCan
from pykiso.lib.connectors.cc_vector_can import CCVectorCan
from pykiso.logging_initializer import LogOptions, add_logging_level
from pykiso.test_coordinator import test_case
from pykiso.test_coordinator.test_case import define_test_parameters
from pykiso.test_setup.dynamic_loader import DynamicImportLinker

# add the internal log levels to avoid errors during unit tests execution
add_logging_level("INTERNAL_WARNING", logging.WARNING + 1)
add_logging_level("INTERNAL_INFO", logging.INFO + 1)
add_logging_level("INTERNAL_DEBUG", logging.DEBUG + 1)

## skip slow test by default
def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


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


@pytest.fixture
def mock_msg(mocker):
    class msg_sub_class(message.Message):
        def __init__(self):
            self.msg_type = 2
            self.sub_type = 1
            self.test_suite = 1
            self.test_case = 1
            self.msg_token = None
            self.error_code = None
            self.reserved = True
            self.tlv_dict = dict()

        serialize = mocker.stub(name="serialize")

    return msg_sub_class()


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
            self.auxiliary_in_use = dut_auxiliary.DUTAuxiliary
            self.connectors = []
            self.auxiliaries = []
            self.suite = unittest.TestSuite()
            self.custom_test_suite = None

        def create_communication_pipeline(self, max_com):
            for _ in range(max_com):
                self.connectors.append(self.channel_in_use())
                self.auxiliaries.append(self.auxiliary_in_use(com=self.connectors[-1]))
                self.auxiliaries[-1].start()
                self.auxiliaries[-1].create_instance()

        def prepare_default_test_cases(self, param):
            @define_test_parameters(
                suite_id=param[0], case_id=param[1], aux_list=param[2]
            )
            class MyTestCase(test_case.BasicTest):
                def test_run(self) -> None:
                    pass

            self.suite.addTest(MyTestCase(methodName="test_run"))

        def prepare_remote_test_cases(self, param):
            @define_test_parameters(
                suite_id=param[0], case_id=param[1], aux_list=param[2]
            )
            class MyTestCase(test_case.RemoteTest):
                pass

            self.suite.addTest(MyTestCase("test_run"))

        def prepare_default_test_suites(self, test_suite_params):
            class MyTestSuite(test_suite.BasicTestSuite):
                def __init__(self, params):
                    super(MyTestSuite, self).__init__(*params)

            # Start integration test
            self.custom_test_suite = MyTestSuite(test_suite_params)

        def stop(self):
            for aux in self.auxiliaries:
                aux.delete_instance()
                aux.stop()

    request.cls.init = InitTestCaseAndSuite()


@pytest.fixture
def ccpcan_inst(mocker):
    class TCChan(CCPCanCan):
        def __init__(self, *args, **kwargs):
            super(TCChan, self).__init__(*args, **kwargs)
            self.remote_id = None

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")

        bus = mocker.stub(name="bus")

    return TCChan(name="test-channel")


@pytest.fixture
def ccvector_inst(mocker):
    class TCChan(CCVectorCan):
        def __init__(self, *args, **kwargs):
            super(TCChan, self).__init__(*args, **kwargs)
            self.remote_id = None

        _cc_open = mocker.stub(name="_cc_open")
        _cc_close = mocker.stub(name="_cc_close")
        _cc_send = mocker.stub(name="_cc_send")
        _cc_receive = mocker.stub(name="_cc_receive")

        bus = mocker.stub(name="bus")

    return TCChan(name="test-channel")


@pytest.fixture
def mock_uds_config(mocker, mock_tp):
    class MockUdsConfig:
        def __init__(self):
            pass

        tp = mock_tp
        send = mocker.stub(name="send")
        rdbi = mocker.stub(name="rdbi")
        disconnect = mocker.stub(name="disconnect")

    return MockUdsConfig()


@pytest.fixture
def mock_tp(mocker):
    class MockTp:
        def __init__(self):
            pass

        encode_isotp = mocker.stub(name=[2, 16, 3, 0, 0, 0, 0, 0])
        decode_isotp = lambda *args, **kwargs: [80, 1, 0, 100, 1, 244]

    return MockTp()


def uds_create_config():
    cfg = """
[can]
interface=peak
canfd=True
baudrate=500000
data_baudrate=2000000
defaultReqId=0xAB
defaultResId=0xAC

[uds]
transportProtocol=CAN
P2_CAN_Client=5
P2_CAN_Server=1

[canTp]
reqId=0xAB
resId=0xAC
addressingType=NORMAL
N_SA=0xFF
N_TA=0xFF
N_AE=0xFF
Mtype=DIAGNOSTICS
discardNegResp=False

[vector]
channel=1
appName=MyApp
    """
    return cfg


@pytest.fixture
def tmp_uds_config_ini(tmp_path):
    uds_folder = tmp_path / "fake_uds"
    uds_folder.mkdir()
    config_ini = uds_folder / "_config.ini"
    config_ini.write_text(uds_create_config())
    return config_ini


TestResult.__test__ = False


@pytest.fixture(scope="function")
def tmp_test(request, tmp_path):
    # use a common tmp_path for all test modules
    tmp_base = tmp_path.parent / "tests"

    log_options = LogOptions(None, "ERROR", None, False)

    aux1, aux2, should_fail = request.param
    ts_folder = tmp_base / f"test_suite_{aux1}_{aux2}"
    ts_folder.mkdir(parents=True)
    tc_file = ts_folder / f"test_{aux1}_{aux2}.py"
    tc_content = create_test_case(aux1, aux2, should_fail)
    tc_file.write_text(tc_content)

    config_file = tmp_base / f"{aux1}_{aux2}.yaml"
    cfg_content = create_config(aux1, aux2, f"test_suite_{aux1}_{aux2}")
    config_file.write_text(cfg_content)

    yield config_file

    # and clean it up afterwards
    shutil.rmtree(str(tmp_base))


def create_config(aux1, aux2, suite_dir):
    cfg = (
        """auxiliaries:
  """
        + aux1
        + """:
    connectors:
        com: chan1
    config: null
    type: pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary
  """
        + aux2
        + """:
    connectors:
        com:   chan2
        flash: chan3
    type: pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary
connectors:
  chan1:
    config: null
    type: pykiso.lib.connectors.cc_example:CCExample
  chan2:
    type: pykiso.lib.connectors.cc_example:CCExample
  chan3:
    config: null
    type: pykiso.lib.connectors.cc_flasher_example:FlasherExample
test_suite_list:
- suite_dir: """
        + suite_dir
        + """
  test_filter_pattern: '*.py'
  test_suite_id: 1
    """
    )
    return cfg


def create_test_case(aux1, aux2, should_fail):
    error = "assert False" if should_fail else "pass"
    tc = (
        """
import pykiso
import logging

from pykiso.auxiliaries import """
        + aux1
        + """, """
        + aux2
        + """


@pykiso.define_test_parameters(
    suite_id=1,
    tag={"variant": ["variant1"], "branch_level": ["daily", "nightly"]},
    aux_list=["""
        + aux1
        + ","
        + aux2
        + """])
class SuiteSetup(pykiso.RemoteTestSuiteSetup):
    pass


@pykiso.define_test_parameters(suite_id=1,
    tag={"variant": ["variant2"], "branch_level": ["daily", "nightly"]},
    aux_list=["""
        + aux1
        + ","
        + aux2
        + """])
class SuiteTearDown(pykiso.RemoteTestSuiteTeardown):
    pass


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=["""
        + aux1
        + """])
class MyTest(pykiso.RemoteTest):
    def test_run(self):
        logging.info("I HAVE RUN 0.1.1!")
        """
        + error
        + """

@pykiso.define_test_parameters(suite_id=1, case_id=2, aux_list=["""
        + aux2
        + """])
class MyTest2(pykiso.BasicTest):
    def test_run(self):
        pass


@pykiso.define_test_parameters(suite_id=1, case_id=3, aux_list=["""
        + aux1
        + """])
class MyTest3(pykiso.BasicTest):
    def test_run(self):
        pass
    """
    )
    return tc
