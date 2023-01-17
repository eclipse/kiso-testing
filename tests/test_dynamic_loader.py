##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys

import pytest

from pykiso.exceptions import ConnectorRequiredError
from pykiso.test_setup.dynamic_loader import DynamicFinder, DynamicImportLinker


@pytest.fixture(scope="module")
def linker(example_module):
    """
    Set up the dynamic linker to provide TestAuxiliaries aux1, aux2, aux3.
    Each of them uses the same TestConnector chan1.
    """
    linker = DynamicImportLinker()
    aux_cfg = {
        "aux11": {
            "config": {"aux_param": 1},
            "connectors": {"com": "chan1"},
            "type": str(example_module) + ":TestAux",
        },
        "aux12": {
            "config": {"aux_param": 2},
            "connectors": {"com": "chan1"},
            "type": str(example_module) + ":TestAux",
        },
        "aux13": {
            "config": {"aux_param": 3},
            "connectors": {"com": "chan1"},
            "type": str(example_module) + ":TestAux",
        },
        "aux_no_class": {
            "connectors": {"com": "chan1"},
            "type": str(example_module),
        },
        "aux_no_file": {
            "connectors": {"com": "chan1"},
            "type": str(example_module)[:-3] + "-nope.py:None",
        },
        "aux_no_connector": {
            "config": {"aux_param": 4},
            "type": str(example_module) + ":TestAuxNoConnector",
        },
        "aux_no_connector_error": {
            "config": {"aux_param": 4},
            "type": str(example_module) + ":TestAux",
        },
    }
    con_cfg = {
        "chan1": {
            "config": {"con_param": 1},
            "type": str(example_module) + ":TestConnector",
        },
    }
    for connector, con_details in con_cfg.items():
        cfg = con_details.get("config") or dict()
        linker.provide_connector(connector, con_details["type"], **cfg)
    for auxiliary, aux_details in aux_cfg.items():
        cfg = aux_details.get("config") or dict()
        try:
            linker.provide_auxiliary(
                auxiliary,
                aux_details["type"],
                aux_cons=aux_details["connectors"],
                **cfg,
            )
        except KeyError:
            linker.provide_auxiliary(
                auxiliary,
                aux_details["type"],
                aux_cons={},
                **cfg,
            )

    linker.install()
    return linker


def test_import_aux(linker):
    from pykiso.auxiliaries import aux11

    assert aux11.__class__.__name__ == "TestAux"


def test_import_aux_cfg(linker):
    from pykiso.auxiliaries import aux11

    assert aux11.kwargs["aux_param"] == 1


def test_import_con_cfg(linker):
    from pykiso.auxiliaries import aux11

    assert aux11.channel.kwargs["con_param"] == 1


def test_import_aux_com(linker):
    from pykiso.auxiliaries import aux11

    assert aux11.channel.__class__.__name__ == "TestConnector"


def test_import_aux_instances(linker):
    from pykiso.auxiliaries import aux11, aux12

    assert aux11 != aux12
    assert aux11.channel == aux12.channel


def test_import_aux_without_connector(linker):
    from pykiso.auxiliaries import aux_no_connector

    assert aux_no_connector.kwargs["aux_param"] == 4
    assert not getattr(aux_no_connector, "channel", False)


def test_import_aux_without_connector_error(linker):
    with pytest.raises(ConnectorRequiredError):
        from pykiso.auxiliaries import aux_no_connector_error


def test_bad_type_spec(linker):
    with pytest.raises(Exception):
        from pykiso.auxiliaries import aux_no_class


def test_module_not_found(linker):
    with pytest.raises(ImportError):
        from pykiso.auxiliaries import aux_no_file


def test_meta_path_order(linker):
    assert [
        index
        for index, finder in enumerate(sys.meta_path)
        if isinstance(finder, DynamicFinder)
    ][0] == 0


def test_import_aux_instanciated(linker):
    from pykiso.auxiliaries import aux11

    assert aux11.is_instance == True
    linker.uninstall()
    assert aux11.is_instance == False
    with pytest.raises(ImportError):
        from pykiso.auxiliaries import aux13
