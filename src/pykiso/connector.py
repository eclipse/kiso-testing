##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Interface Definition for Connectors, CChannels and Flasher
**********************************************************

:module: connector

:synopsis: Interface for a channel

.. currentmodule:: connector


"""
import abc
import multiprocessing
import pathlib
import threading

from .types import MsgType, PathType


class Connector(abc.ABC):
    """Abstract interface for all connectors to inherit from.

    Defines hooks for opening and closing the connector and
    also defines a contextmanager interface."""

    def __init__(self, name: str = None):
        """Constructor.

        :param name: alias for the connector, used for ``repr`` and logging.
        """
        super().__init__()
        self.name = name

    def __repr__(self):
        name = self.name
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, typ, value, traceback):
        self.close()
        if value is not None:
            raise value

    @abc.abstractmethod
    def open(self):
        """Initialise the Connector."""
        pass

    @abc.abstractmethod
    def close(self):
        """Close the connector, freeing resources."""
        pass


class CChannel(Connector):
    """Abstract class for coordination channel."""

    def __init__(self, processing=False, **kwargs: dict) -> None:
        """Constructor.

        :param processing: if multiprocessing object is used.
        """
        super().__init__(**kwargs)
        if processing:
            self._lock_tx = multiprocessing.RLock()
            self._lock_rx = multiprocessing.RLock()
            self._lock = multiprocessing.Lock()
        else:
            self._lock_tx = threading.RLock()
            self._lock_rx = threading.RLock()
            self._lock = threading.Lock()

    def open(self) -> None:
        """Open a thread-safe channel."""
        with self._lock:
            self._cc_open()

    def close(self) -> None:
        """Close a thread-safe channel."""
        with self._lock:
            self._cc_close()

    def cc_send(self, msg: MsgType, raw: bool = False, **kwargs) -> None:
        """Send a thread-safe message on the channel and wait for an acknowledgement.

        :param msg: message to send
        :param raw: should the message be converted as pykiso.Message
            or sent as it is
        :param kwargs: named arguments
        """
        with self._lock_tx:
            self._cc_send(msg=msg, raw=raw, **kwargs)

    def cc_receive(self, timeout: float = 0.1, raw: bool = False) -> dict:
        """Read a thread-safe message on the channel and send an acknowledgement.

        :param timeout: time in second to wait for reading a message
        :param raw: should the message be returned as pykiso.Message or
            sent as it is

        :return: the received message
        """
        with self._lock_rx:
            return self._cc_receive(timeout=timeout, raw=raw)

    @abc.abstractmethod
    def _cc_open(self) -> None:
        """Open the channel."""
        pass

    @abc.abstractmethod
    def _cc_close(self) -> None:
        """Close the channel."""
        pass

    @abc.abstractmethod
    def _cc_send(self, msg: MsgType, raw: bool = False, **kwargs) -> None:
        """Sends the message on the channel.

        :param msg: Message to send out
        :param raw: send raw message without further work (default: False)
        :param kwargs: named arguments
        """
        pass

    @abc.abstractmethod
    def _cc_receive(self, timeout: float, raw: bool = False) -> dict:
        """How to receive something from the channel.

        :param timeout: Time to wait in second for a message to be received
        :param raw: send raw message without further work (default: False)

        :return: message.Message() - If one received / None - If not
        """
        pass


class Flasher(Connector):
    """Interface for devices that can flash firmware on our targets."""

    def __init__(self, binary: PathType = None, **kwargs):
        """Constructor.

        :param binary: binary firmware file

        :raise ValueError: if binary doesn't exist or is not a file
        :raise TypeError: if given binary is None
        """
        super().__init__(**kwargs)
        if binary is not None:
            binary = pathlib.Path(binary).resolve()  # force an absolute path
            if binary.exists() and binary.is_file():
                self.binary = binary
            else:
                raise ValueError(
                    f"'binary' must be a path-like object to an existing file (got {binary})"
                )
        else:
            raise TypeError("'binary' must be a path-like object, not None")

    @abc.abstractmethod
    def flash(self):
        """Flash firmware on the target."""
        pass
