import pytest


@pytest.mark.xray("BDU3-13141")
def test_xray0():
    assert True
    assert True
    assert True


def test_xray1():
    assert not False


def test_xray2():
    assert True
