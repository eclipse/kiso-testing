import time

import pytest


def test_xray0():
    """Description 0"""
    time.sleep(4)
    assert True


@pytest.mark.test_key("BDU3-13141")
def test_xray1():
    """Description 1"""
    time.sleep(0.5)
    assert False


@pytest.mark.test_key("BDU3-13302")
def test_xray2():
    """Description 2"""
    time.sleep(2)
    assert True


@pytest.mark.skip(reason="no way of currently testing this")
@pytest.mark.test_key("BDU3-13303")
def test_xray3():
    """Description 3"""
    time.sleep(3)
    assert True
