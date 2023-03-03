import pytest

from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface


@pytest.hookspec(firstresult=True)
def pytest_auxiliary_start(aux: DTAuxiliaryInterface):
    return aux.create_instance()


@pytest.hookspec(firstresult=True)
def pytest_auxiliary_stop(aux: DTAuxiliaryInterface):
    return aux.delete_instance()
