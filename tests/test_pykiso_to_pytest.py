##########################################################################
# Copyright (c) 2010-2023 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import pytest
from click.testing import CliRunner

from pykiso.tool.pykiso_to_pytest.cli import find_string_in, format_value, get_imports, main, nested_get, remove_key


@pytest.fixture
def pykiso_config():
    return {
        "auxiliaries": {
            "aux1": {
                "connectors": {"com": "chan1"},
                "config": None,
                "type": "pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary",
            },
        },
        "connectors": {
            "chan1": {
                "config": None,
                "type": "pykiso.lib.connectors.cc_example:CCExample",
            },
        },
    }


@pytest.fixture
def pykiso_config_proxy_auxiliary():
    return {
        "auxiliaries": {
            "proxy_aux": {
                "connectors": {"com": "can_channel"},
                "config": {
                    "aux_list": ["aux1"],
                    "activate_trace": False,
                    "trace_dir": "kiso-testing\\examples\\templates\\suite_proxy",
                    "trace_name": "can_trace",
                    "auto_start": False,
                },
                "type": "pykiso.lib.auxiliaries.proxy_auxiliary:ProxyAuxiliary",
            },
            "aux1": {
                "connectors": {"com": "proxy_com1"},
                "config": {"auto_start": False},
                "type": "pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary",
            },
        },
        "connectors": {
            "proxy_com1": {
                "config": None,
                "type": "pykiso.lib.connectors.cc_proxy:CCProxy",
            },
            "can_channel": {
                "config": {
                    "interface": "pcan",
                    "channel": "PCAN_USBBUS1",
                    "state": "ACTIVE",
                    "remote_id": 768,
                },
                "type": "pykiso.lib.connectors.cc_pcan_can:CCPCanCan",
            },
        },
    }


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize(
    "value,expected", [(23, 23), ("test", '"test"'), ([233, 23], [233, 23])]
)
def test_format_value(value, expected):
    assert format_value(value) == expected


@pytest.mark.parametrize(
    "dict_test,key_expected",
    [
        ({"test": "value1", "test2": "value2"}, ("test",)),
        ({"test": {"key1": "value1"}, "test2": "value2"}, ("test", "key1")),
        ({"test": "value", "test2": "value2"}, None),
    ],
)
def test_find_string_in(dict_test, key_expected):

    key = find_string_in(dict_test, "value1")

    assert key == key_expected


@pytest.mark.parametrize("copy", [True, False])
def test_nested_get(copy):
    dict_test = {"test": {"key1": "value1"}, "test2": "value2"}

    dict_get = nested_get(dict_test, ["test"], copy=copy)

    assert dict_get == dict_test["test"]


def test_remove_key():
    dict_test = {"test": {"key1": "value1"}, "test2": "value2"}

    remove_key(dict_test, key_path=["test", "key1"])

    assert dict_test["test"] == {}


def test_get_imports(tmp_path):
    path_file = tmp_path / "import_test.py"
    import_to_write = [
        "from pykiso.lib.auxiliaries.communication_auxiliary import CommunicationAuxiliary\n",
        "from pykiso.lib.auxiliaries.proxy_auxiliary import ProxyAuxiliary\n",
        "from pykiso.lib.connectors.cc_pcan_can import CCPCanCan\n",
        "from pykiso.lib.connectors.cc_proxy import CCProxy\n",
    ]
    with open(path_file, "w", encoding="utf8") as file:
        file.write("".join(import_to_write))

    imports = get_imports(path_file)

    assert imports == import_to_write


def test_main(mocker, tmp_path, pykiso_config, runner):
    name_file = "conf"
    path_output = tmp_path / name_file
    parse_config = mocker.patch(
        "pykiso.config_parser.parse_config", return_value=pykiso_config
    )

    with runner.isolated_filesystem(temp_dir=tmp_path) as f:
        with open("config.yaml", "w") as f:
            pass
        result = runner.invoke(main, ["config.yaml", f"-d{path_output}"])
        with open(tmp_path / f"{name_file}.py", "r") as f:
            lines = f.readlines()

    parse_config.assert_called_once()
    assert "".join(
        [
            "from pykiso.lib.auxiliaries.dut_auxiliary import DUTAuxiliary\n",
            "from pykiso.lib.connectors.cc_example import CCExample\n",
            "\n",
            "\n",
            '@pytest.fixture(scope="session")\n',
            "def aux1():\n",
            "    try:\n",
            '        com = CCExample(name="chan1")\n',
            "        aux1 = DUTAuxiliary(\n",
            "            com=com,\n",
            "        )\n",
            "        aux1.start()\n",
            "        aux1.create_instance()\n",
            "    except Exception:\n",
            '        logging.exception("something bad happened")\n',
            "    yield aux1\n",
            "    aux1.delete_instance()\n",
            "    aux1.stop()\n",
        ]
    ) in "".join(lines)
    assert result.exit_code == 0


def test_main_proxy_aux(tmp_path, mocker, pykiso_config_proxy_auxiliary, runner):
    dir_name = "conf"
    path_output = tmp_path / dir_name
    path_output.mkdir()
    parse_config = mocker.patch(
        "pykiso.config_parser.parse_config", return_value=pykiso_config_proxy_auxiliary
    )

    with runner.isolated_filesystem(temp_dir=tmp_path) as f:
        with open("config.yaml", "w") as f:
            pass
        result = runner.invoke(main, ["config.yaml", f"-d{path_output}"])

        with open(path_output / "conftest.py", "r") as f:
            lines = f.readlines()

    parse_config.assert_called_once()
    assert "".join(
        [
            "from pykiso.lib.auxiliaries.communication_auxiliary import CommunicationAuxiliary\n",
            "from pykiso.lib.auxiliaries.proxy_auxiliary import ProxyAuxiliary\n",
            "from pykiso.lib.connectors.cc_pcan_can import CCPCanCan\n",
            "from pykiso.lib.connectors.cc_proxy import CCProxy\n",
            "\n",
            "\n",
            '@pytest.fixture(scope="session")\n',
            "def aux1():\n",
            "    try:\n",
            '        com = CCProxy(name="proxy_com1")\n',
            "        aux1 = CommunicationAuxiliary(\n",
            "            com=com,\n",
            "            auto_start=False,\n",
            "        )\n",
            "        aux1.start()\n",
            "        aux1.create_instance()\n",
            "    except Exception:\n",
            '        logging.exception("something bad happened")\n',
            "    yield aux1\n",
            "    aux1.delete_instance()\n",
            "    aux1.stop()\n",
            "\n",
            "\n",
            '@pytest.fixture(scope="session")\n',
            "def proxy(\n",
            "    aux1,\n",
            "):\n",
            "    channel = CCPCanCan(\n",
            '        name="can_channel",\n',
            '        interface="pcan",\n',
            '        channel="PCAN_USBBUS1",\n',
            '        state="ACTIVE",\n',
            "        remote_id=768,\n",
            "    )\n",
            "\n",
            '    proxy_aux = ProxyAuxiliary(name="proxy_aux", com=channel, aux_list=["aux1"])\n',
            "    proxy_aux.start()\n",
            "    proxy_aux.create_instance()\n",
            "    yield aux1, proxy_aux\n",
            "    proxy_aux.delete_instance()\n",
            "    proxy_aux.stop()\n",
        ]
    ) in "".join(lines)
    assert result.exit_code == 0
