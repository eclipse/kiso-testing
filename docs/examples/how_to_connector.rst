.. _how_to_create_connector:

How to create a connector
=========================

On pykiso view, a connector is the communication medium between the
auxiliary and the device under test. It can consist of two different blocks:

- a **communication channel**
- a **flasher**

Thus, its goal is to implement the
sending and reception of data on the lower level protocol layers
(e.g. CAN, UART, UDP).

Both can be used as context managers as they inherit the common interface
:py:class:`~pykiso.connector.Connector`.

.. note::
  Many already implemented connectors are available under :py:mod:`pykiso.lib.connectors`.
  and can easily be adapted for new implementations.


Communication Channel
~~~~~~~~~~~~~~~~~~~~~

In order to facilitate the implementation of a communication channel and to ensure
the compatibility with different auxiliaries, pykiso provides a common
interface :py:class:`~pykiso.connector.CChannel`.

This interface enforces the implementation of the following methods:

- :py:meth:`~pykiso.connector.CChannel._cc_open`: open the communication.
  Does not take any argument.
- :py:meth:`~pykiso.connector.CChannel._cc_close`: close the communication.
  Does not take any argument.
- :py:meth:`~pykiso.connector.CChannel._cc_send`: send data if the communication is open.
  Requires one positional argument ``msg`` and one keyword argument ``raw``, used to serialize the data
  before sending it.
- :py:meth:`~pykiso.connector.CChannel._cc_receive`: receive data if the communication is open.
  Requires one positional argument ``timeout`` and one keyword argument ``raw``, used to deserialize
  the data when receiving it.


Class definition and instanciation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a new communication channel, the first step is to define its class
and constructor.

Let's admin that the following code is added to a file called **my_connector.py**:

.. code:: python

    import pykiso

    MyCommunicationChannel(pykiso.CChannel):

        def __init__(self, arg1, arg2, kwarg1 = "default"):
            ...

Then, if this CChannel has to be used within a test, the test configuration file
will derive from its location and constructor parameters:

.. code:: yaml

    connectors:
      my_chan:
        # provide the constructor parameters
        config:
          # arg1 and arg2 are mandatory as we defined them as positional arguments
          arg1: value for positional argument arg1
          arg2: value for positional argument arg2
          # kwarg1 is optional as we defined it as a keyword argument with a default value
          kwarg1: different value for keyword argument kwarg1
        # let pykiso know which class we want to instantiate with the provided parameters
        type: path/to/my_connector.py:MyCommunicationChannel


.. note::
    If this file is located inside an installable package ``my_package``,
    the type will become ``type: my_package.my_connector:MyCommunicationChannel``.


Interface completion
^^^^^^^^^^^^^^^^^^^^

If the code above is left as such, it won't be usable as a connector as
the communication channel's abstract methods aren't implemented.

Therefore, all four methods ``_cc_open``, ``_cc_close``, ``_cc_send`` and
``_cc_receive`` need to be implemented.

In order to complete the code above, let's assume that a module *my_connection_module*
implements the communication logic.

The connector then becomes:

.. code:: python

    from my_connection_module import Connection
    import pykiso

    MyCommunicationChannel(pykiso.CChannel):

        def __init__(self, arg1, arg2, kwarg1 = "default"):
            # Connection class could be anything, like serial.Serial or socket.socket
            self.my_connection = Connection(arg1, arg2)

        def _cc_open(self):
            self.my_connection.open()

        def _cc_close(self):
            self.my_connection.close()

        def _cc_send(self, data: Union[Data, bytes], raw = False):
            if raw:
                data_bytes = data
            else:
                data_bytes = data.serialize()
            self.my_connection.send(data_bytes)

        def _cc_receive(self, timeout, raw = False):
            received_data = self.my_connection.receive(timeout=timeout)
            if received_data:
                if not raw:
                    data = Data.deserialize(received_data)
                return data

.. note::
    The API used in this example for the fictive *my_connection* module
    entirely depends on the used module.

Parameters and return values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to stay compatible and usable by the attached auxiliary, the created connector
has to respect certain rules (in addition to the CChannel base class interface):

- **rule 1** : _cc_receive concrete implementation has to return a dictionary containing
  at least the key "msg". If more than the data received is return, for example the CAN ID
  from the emitter, just put it in the return dictionary.

see the example below with the cc_pcan_can connector and the return of the remote_id value :

.. code:: python

    def _cc_receive(
        self, timeout: float = 0.0001, raw: bool = False
    ) -> Dict[str, Union[MessageType, int]]:
        """Receive a can message using configured filters.

        If raw parameter is set to True return received message as it is (bytes)
        otherwise test entity protocol format is used and Message class type is returned.

        :param timeout: timeout applied on reception
        :param raw: boolean use to select test entity protocol format

        :return: the received data and the source can id
        """
        try:  # Catch bus errors & rcv.data errors when no messages where received
            received_msg = self.bus.recv(timeout=timeout or self.timeout)

            if received_msg is not None:
                frame_id = received_msg.arbitration_id
                payload = received_msg.data
                timestamp = received_msg.timestamp
                if not raw:
                    payload = Message.parse_packet(payload)
                log.debug(f"received CAN Message: {frame_id}, {payload}, {timestamp}")
                return {"msg": payload, "remote_id": frame_id}
            else:
                return {"msg": None}
        except can.CanError as can_error:
            log.debug(f"encountered can error: {can_error}")
            return {"msg": None}
        except Exception:
            log.exception(f"encountered error while receiving message via {self}")
            return {"msg": None}


- **rule 2** : additional arguments associated to _cc_send concret implementation has
  to be named arguments and used the **kwargs

see example below with the cc_pcan_can connector and the additional remote_id parameter:

.. code:: python

    def _cc_send(self, msg: MessageType, raw: bool = False, **kwargs) -> None:
        """Send a CAN message at the configured id.

        If remote_id parameter is not given take configured ones, in addition if
        raw is set to True take the msg parameter as it is otherwise parse it using
        test entity protocol format.

        :param msg: data to send
        :param raw: boolean use to select test entity protocol format
        :param kwargs: named arguments

        """
        _data = msg
        remote_id = kwargs.get("remote_id")

        if remote_id is None:
            remote_id = self.remote_id

Flasher
~~~~~~~

pykiso provides a common interface for flashers :py:class:`~pykiso.connector.Flasher`
that aims to be as simple as possible.

It only consists of 3 methods to implement:

- :py:meth:`~pykiso.connector.Flasher.open`: open the communication with the flashing hardware
  if any (for e.g. JTAG flashing) and perform any preliminaly action
- :py:meth:`~pykiso.connector.Flasher.flash`: perform all actions to flash the target device
- :py:meth:`~pykiso.connector.Flasher.close`: close the communication with the flashing hardware.

.. note::
    To ensure that a Flasher is closed after being opened, it should be used as a context manager
    (see :ref:`aux-tutorial-example`).
