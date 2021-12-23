How to create a connector
-------------------------

On pykiso view, a connector is the communication medium between the
auxiliary and the device under test. It can consist of two different blocks:

- a **communication channel**
- a **flasher**

Thus, its goal is to implement the
sending and reception of data on the lower level protocol layers
(e.g. CAN, UART, UDP).

Both can be used as context managers as they inherit the common interface
Connector (:py:class:`pykiso.connector.Connector`).

Communication Channel
~~~~~~~~~~~~~~~~~~~~~

In order to facilitate the implementation of a communication channel and to ensure
the compatibility with different auxiliaries, pykiso provides a common
interface CChannel (:py:class:`pykiso.connector.CChannel`).

This interface enforces the implementation of the following methods:

- ``_cc_open`` (:py:meth:`pykiso.connector.CChannel._cc_open`): open the communication.
  Does not take any argument.
- ``_cc_close`` (:py:meth:`pykiso.connector.CChannel._cc_close`): close the communication.
  Does not take any argument.
- ``_cc_send`` (:py:meth:`pykiso.connector.CChannel._cc_send`): send data if the communication is open.
  Requires one positional argument ``msg`` and one keyword argument ``raw``.
- ``_cc_receive`` (:py:meth:`pykiso.connector.CChannel._cc_receive`): receive data if the communication is open.
  Requires one positional argument ``timeout`` and one keyword argument ``raw``.


Class definition and instanciation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a new communication channel, the first step is to define its class
and constructor.

Let's admin that, the following code is added to a file called **my_connector.py**:

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

Completing the code above:

.. code:: python

    from my_connection_module import Connection
    import pykiso

    MyCommunicationChannel(pykiso.CChannel):

        def __init__(self, arg1, arg2, kwarg1 = "default"):
            # Connection can be anything, like serial.Serial or
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
