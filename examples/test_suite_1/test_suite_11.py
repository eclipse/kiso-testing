import pytest


@pytest.fixture(scope="function")
def aux1(aux1):
    yield aux1


@pytest.fixture(scope="function")
def aux2(aux2):
    yield aux2


def test_something(aux1, aux2):
    assert aux1.create_instance() == True


def test_will_pass(aux1, mocker):
    mocker.patch.object(aux1, "create_instance", return_value="BLA")
    assert aux1.create_instance() == "BLA"
