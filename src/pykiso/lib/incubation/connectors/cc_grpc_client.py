##########################################################################
# Copyright (c) 2023-2023 Accenture GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via GRPC
******************************

:module: cc_grpc_client

:synopsis: Grpc communication channel

.. currentmodule:: cc_grpc_client

list of todo items:
* Extend by supporting a path instead of files so that many proto files can be used
* Extend with security capabilities

"""

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Dict, Optional

import grpc

from pykiso import connector

log = logging.getLogger(__name__)


class CCGrpcClient(connector.CChannel):
    """Grpc client implementation"""

    def __init__(
        self,
        dest_ip: str,
        dest_port: int,
        generated_protobuf_data_types_file: str,
        generated_protobuf_grpc_file: str,
        default_service_name: str,
        default_rpc_name: str,
        default_message_name: str,
        default_message_fields: dict,
        **kwargs,
    ):
        """Instantiate a grpc client

        :param dest_ip (str): grpc server ip address
        :param dest_port (int): grpc server port
        :param generated_protobuf_data_types_file (str): path to the generated protobuf data types file
        :param generated_protobuf_grpc_file (str): path to the generated protobuf grpc file
        :param default_service_name (str): default service name to use
        :param default_rpc_name (str): default rpc name to use
        :param default_message_name (str): default message name to use
        :param default_message_fields (dict): default parameters to use in dictionary format
        """
        # Initialize the super class
        super().__init__(**kwargs)
        # Initialize the grpc client
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        # Import the generated datamodel protobuf file
        spec = importlib.util.spec_from_file_location(
            Path(generated_protobuf_data_types_file).stem,
            Path(generated_protobuf_data_types_file),
        )
        self.grpc_datamodel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.grpc_datamodel)
        # Import the generated grpc protobuf file
        # Import the module
        spec = importlib.util.spec_from_file_location(
            Path(generated_protobuf_grpc_file).stem,
            Path(generated_protobuf_grpc_file),
        )
        self.grpc_stub_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.grpc_stub_module)
        # Extract the stubs
        module_attributes = inspect.getmembers(self.grpc_stub_module, inspect.isclass)
        self.grpc_stub = []
        for attribute in module_attributes:
            if attribute[0].endswith("Stub"):
                self.grpc_stub.append(attribute[1])
        # Prepare the empty stub list. It will be used for binding the stubs to the channel
        self.stubs = {}

        # Set the default rpc and message
        self.default_service_name = default_service_name
        self.default_rpc_name = default_rpc_name
        self.default_message_name = default_message_name
        self.default_message_fields = default_message_fields
        self.list_of_received_messages = []

    def _cc_open(self) -> None:
        """Open the grpc connection to server."""
        self.channel = grpc.insecure_channel(self.dest_ip + ":" + str(self.dest_port))
        # Bind stubs to new channel
        self.stubs = dict([(stub.__name__[:-4], stub(self.channel)) for stub in self.grpc_stub])
        # Validate at least that most of the default parameters are valid
        try:
            if self.default_service_name not in self.stubs:
                raise ValueError(f"{self.default_service_name=} was not found!")
            if not hasattr(self.stubs[self.default_service_name], self.default_rpc_name):
                raise ValueError(f"{self.default_rpc_name=} was not found!")
            if not hasattr(self.grpc_datamodel, self.default_message_name):
                raise ValueError(f"{self.default_message_name=} was not found!")
            message_class = getattr(self.grpc_datamodel, self.default_message_name)
            message_class(**self.default_message_fields)
        except TypeError as e:
            self._cc_close()
            raise ValueError(f"{self.default_message_fields=} was not valid!") from e
        except Exception as e:
            self._cc_close()
            raise e

    def _cc_close(self) -> None:
        """Close the grpc connection to server."""
        self.stubs.clear()
        self.channel.close()

    def _cc_send(self, msg: bytes, **kwargs) -> None:
        """Send message to grpc server.

        :param msg: message to send, should bytes.
        :param kwargs: used to extract the service_name, rpc_name, message_name and message_fields

        In addition to the message, the following keyword arguments are supported:

            - rpc_name: name of the rpc to trigger
            - message_name: name of the message to use
            - message_fields: attributes to use in dictionary format

        """
        # Extract needed parameters or the default once
        service_name = kwargs.get("service_name", self.default_service_name)
        rpc_name = kwargs.get("rpc_name", self.default_rpc_name)
        message_name = kwargs.get("message_name", self.default_message_name)
        # For the message attributes, we have 3 possibilities:
        # * msg is populated OR
        # * message_fields is populated OR
        # * the default message attributes are used
        message_fields = msg if msg else kwargs.get("message_fields", self.default_message_fields)

        # Now, the validity of the parameters need to be checked
        # First we check that the service_name exist
        if service_name not in self.stubs:
            log.warning(f"{service_name=} was not found! Fallback to {self.default_service_name=}")
            service_name = self.default_service_name
        # Then we check that the rpc_name exist
        if not hasattr(self.stubs[service_name], rpc_name):
            log.warning(f"{rpc_name=} was not found! Fallback to {self.default_rpc_name=}")
            rpc_name = self.default_rpc_name
        # Then we check that the message_name exist
        if not hasattr(self.grpc_datamodel, message_name):
            log.warning(f"{message_name=} was not found! Fallback to {self.default_message_name=}")
            message_name = self.default_message_name
        # The message constitution will be checked later on, when the message will be sent

        # Trigger the rpc
        rpc_method = getattr(self.stubs[service_name], rpc_name)
        message_class = getattr(self.grpc_datamodel, message_name)
        result = self._rpc_trigger(rpc_method, message_class, message_fields)

        # Store the result
        self.list_of_received_messages.append(result)

    def _rpc_trigger(self, rpc_method: str, message_class: str, message_fields: dict = None) -> None:
        """Trigger the rpc.

        :param rpc_method: rpc method to trigger
        :param message_class: message class to use
        :param message_fields: attributes to use in dictionary format

        :return: result of the rpc
        """
        try:
            if message_fields:
                return rpc_method(message_class(**message_fields))
            else:
                return rpc_method(message_class())
        except Exception as e:
            log.exception(f"Error while triggering rpc: {e}")
            return None

    def _cc_receive(self, timeout: float = 1e-6) -> Dict[str, Optional[bytes]]:
        """Read message from socket.

        :param timeout: timeout applied on receive event

        :return: dictionary containing the received bytes if successful, otherwise None
        """

        try:
            return {"msg": self.list_of_received_messages.pop(0)}
        except IndexError:
            log.debug(f"no message received via {self}")
            return {"msg": None}
