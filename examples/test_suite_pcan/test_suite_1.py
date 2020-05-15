import pykiso
import logging

from pykiso.auxiliaries import can_aux


@pykiso.define_test_case_parameters(0, 1, 1, [can_aux])
class MyTest(pykiso.BasicTest):
    def test_run(self):
        can_aux.send_message(b"Hello")


@pykiso.define_test_case_parameters(0, 1, 2, [can_aux])
class MyTest2(pykiso.BasicTest):
    def test_run(self):
        reply = can_aux.receive_message()
        print(f"{reply}")
