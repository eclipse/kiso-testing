import pytest
from pykiso.dynamic_loader import DynamicImportLinker


@pytest.fixture
def com_aux_linker():
    linker = DynamicImportLinker()
    aux_conf = {
        "com_aux": {
            "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            "connectors": {"com": "loopback"},
        },
    }
    con_conf = {
        "loopback": {"type": "pykiso.lib.connectors.cc_raw_loopback:CCLoopback"}
    }
    for connector, con_details in con_conf.items():
        cfg = con_details.get("config") or dict()
        linker.provide_connector(connector, con_details["type"], **cfg)
    for auxiliary, aux_details in aux_conf.items():
        cfg = aux_details.get("config") or dict()
        linker.provide_auxiliary(
            auxiliary, aux_details["type"], aux_cons=aux_details["connectors"], **cfg,
        )
    linker.install()
    yield linker
    linker.uninstall()


def test_com_aux_messaging(com_aux_linker):
    from pykiso.auxiliaries import com_aux

    msg = b"test"
    assert com_aux.send_message(msg)
    rec_msg = com_aux.receive_message()
    assert rec_msg == msg
