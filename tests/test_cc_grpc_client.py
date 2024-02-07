##########################################################################
# Copyright (c) 2023-2023 Accenture
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import socket
from concurrent import futures
from pathlib import Path

import grpc
import pytest

# Import the generated protobuf files
from grpc_test_files import helloworld_pb2, helloworld_pb2_grpc

from pykiso.lib.incubation.connectors.cc_grpc_client import CCGrpcClient


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)


@pytest.fixture(scope="module")
def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    yield server
    server.stop(1)


@pytest.fixture
def grpc_inst(serve):
    grpc_inst = CCGrpcClient(
        "127.0.0.1",
        50051,
        Path(__file__).parent / "grpc_test_files" / "helloworld_pb2.py",
        Path(__file__).parent / "grpc_test_files" / "helloworld_pb2_grpc.py",
        "Greeter",
        "SayHello",
        "HelloRequest",
        {"name": "World"},
    )
    yield grpc_inst


def test_constructor_invalid():
    """Test invalid construct with no parameters given"""
    with pytest.raises(TypeError):
        CCGrpcClient()


def test_constructor_valid(grpc_inst):
    """Test a valid constructor call with valid ip and port."""
    grpc_inst: CCGrpcClient = grpc_inst
    assert str("helloworld_pb2_grpc.GreeterStub") in str(grpc_inst.grpc_stub[0])
    assert hasattr(grpc_inst.grpc_datamodel, "HelloRequest")


def test_open_channel(grpc_inst):
    """Test message _cc_open method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    assert grpc_inst.channel is not None


def test_open_channel_with_invalid_default(grpc_inst):
    # Modify the default parameters to be invalid
    grpc_inst: CCGrpcClient = grpc_inst
    # Invalid service name
    grpc_inst.default_service_name = "ServiceFail"
    with pytest.raises(ValueError):
        grpc_inst._cc_open()
    grpc_inst.default_service_name = "Greeter"
    # Invalid rpc name
    grpc_inst.default_rpc_name = "RpcFail"
    with pytest.raises(ValueError):
        grpc_inst._cc_open()
    grpc_inst.default_rpc_name = "SayHello"
    # Invalid message name
    grpc_inst.default_message_name = "MessageFail"
    with pytest.raises(ValueError):
        grpc_inst._cc_open()
    grpc_inst.default_message_name = "HelloRequest"
    # Invalid message parameter
    grpc_inst.default_message_fields = {"data": "WorldFail"}
    with pytest.raises(ValueError):
        grpc_inst._cc_open()
    grpc_inst.default_message_fields = ""
    with pytest.raises(ValueError):
        grpc_inst._cc_open()
    grpc_inst.default_message_fields = {"name": "World"}


def test_close_channel(grpc_inst):
    """Test message _cc_close method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_close()
    assert not grpc_inst.stubs


def test_send_message_valid(grpc_inst):
    """Test message _cc_send method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_send(
        None, service_name="Greeter", rpc_name="SayHello", message_name="HelloRequest"
    )
    assert "Hello, World!" in str(grpc_inst.list_of_received_messages[0])


def test_send_message_service_invalid(grpc_inst):
    """Test message _cc_send method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_send(
        None,
        service_name="GreeterFail",
        rpc_name="SayHello",
        message_name="HelloRequest",
    )
    assert "Hello, World!" in str(grpc_inst.list_of_received_messages[0])


def test_send_message_rpc_invalid(grpc_inst):
    """Test message _cc_send method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_send(
        None,
        service_name="Greeter",
        rpc_name="SayHelloFail",
        message_name="HelloRequest",
    )
    assert "Hello, World!" in str(grpc_inst.list_of_received_messages[0])


def test_send_message_message_invalid(grpc_inst):
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_send(
        None,
        service_name="Greeter",
        rpc_name="SayHello",
        message_name="HelloRequestFail",
    )
    assert "Hello, World!" in str(grpc_inst.list_of_received_messages[0])


def test_send_message_failed(grpc_inst, mocker):
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    mocker.patch.object(grpc_inst.stubs["Greeter"], "SayHello", side_effect=Exception)
    grpc_inst._cc_send(
        None,
        service_name="Greeter",
        rpc_name="SayHello",
        message_name="HelloRequestFail",
    )
    assert not grpc_inst.list_of_received_messages[0]


def test_receive_message_valid(grpc_inst):
    """Test message _cc_receive method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    grpc_inst._cc_send(None, rpc_name="SayHello", message_name="HelloRequest")
    return_value = grpc_inst._cc_receive()
    assert "Hello, World!" in str(return_value["msg"])


def test_receive_message_no_value(grpc_inst):
    """Test message _cc_receive method."""
    grpc_inst: CCGrpcClient = grpc_inst
    grpc_inst._cc_open()
    assert grpc_inst._cc_receive() == {"msg": None}
