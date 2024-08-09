.. _how_to_create_aux:

How to create an auxiliary
==========================

This tutorial aims to explain the working principle of an Auxiliary by
providing information on available Auxiliary interface, their purpose
and the implementation of new auxiliaries.

To provide hints on the implementation of an Auxiliary, an example that
implements a generic auxiliary is provided, that is not usable but shall
explain the different concepts and implementation steps.

Auxiliary interface and the use-cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pykiso provides one auxiliary interface, which is used as basis for
any implemented auxiliary. The interface aims to cover every
possible usage of an auxiliary:

- The :py:class:`~pykiso.auxiliary.AuxiliaryInterface`
  is a double threaded base auxiliary, where one thread is used for the transmission
  and a second for the reception. It is suited for IO-bound tasks where
  the reception of data cannot be expected.

Execution of an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~~~~

Auxiliary creation and deletion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any auxiliary is **created** at test setup (before any test case is executed) by calling :py:meth:`~pykiso.auxiliary.AuxiliaryInterface.create_instance`
and **deleted** at test teardown (after all test cases have been executed) by calling :py:meth:`~pykiso.auxiliary.AuxiliaryInterface.delete_instance`.

These methods set the :py:attr:`is_instance attribute <pykiso.auxiliary.AuxiliaryInterface.is_instance>` that
indicated if the auxiliary is running correctly.

Concurrent auxiliary execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The execution of concurrent auxiliaries, everything related to the tansmission is handled by
:py:meth:`~pykiso.auxiliary.AuxiliaryInterface._transmit_task` and for the reception
by :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._reception_task`

Each command execution is handled in a thread-safe way by getting values from an input queue and
returning the command result in an output queue.

Auxiliary run
^^^^^^^^^^^^^

Each time the execution is entered, the following actions are performed:

1. Verify if a request is available in the input queue

  #. If the command message is "DELETE_AUXILIARY" the transmit task while loop ends

  #. If the command message is a tuple of 2 elements starting with your custom command type, and then the data to send. This custom command has to be implemented in the :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._run_command` method.

2. Verify if a Message is available for reception

  #. Call the auxiliarie's :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._receive_message` and simply wait for a message coming from the connector.

  #. If something is returned, put it in the output queue, otherwise repeat this execution cycle.

Implement an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~

Common auxiliary methods
^^^^^^^^^^^^^^^^^^^^^^^^

The Auxiliary interface require the same abstract methods
to be implemented:

- :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._create_auxiliary_instance`:
  handle the auxiliary creation. Minimal actions to perform are
  opening the attached :py:class:`~pykiso.connector.CChannel`, to which can be added actions such as flashing the device under test,
  perform security related operations to allow the communication, etc.
- :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._delete_auxiliary_instance`:
  handle the auxiliary deletion. This method is the counterpart of
  ``_create_auxiliary_instance``, so it needs to be implemented in a way that ``_create_auxiliary_instance``
  can be called again without side effects. In the most basic case, it should at least close the opened :py:class:`~pykiso.connector.CChannel`.

Concurrent auxiliary methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to the previously described methods, the concurrent Auxiliary
interface :py:class:`~pykiso.auxiliary.AuxiliaryInterface` require
the following methods to be implemented:

- :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._run_command`: implement the different commands that should be performed by the Auxiliary.
- :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._receive_message`: implement the reception of data. This method should at least call the CChannel's
  :py:meth:`~pykiso.connector.CChannel.cc_receive` method. The received data can then be decoded according to a particular protocol, matched
  against a previously sent request, or trigger any kind of further processing.

- :py:meth:`~pykiso.auxiliary.AuxiliaryInterface._abort_command`: is not mandatory. Implement the command abortion mechanism. This mechanism **must also be implemented
  on the target device**.

.. _aux-tutorial-example:

Auxiliary implementation example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See below an example implementing the basic functionalities of a Thread Auxiliary:

.. code:: python

    import logging
    from pykiso import AuxiliaryInterface, CChannel, Flasher

    # this auxiliary is thread-based, so it must inherit AuxiliaryInterface
    class MyAuxiliary(AuxiliaryInterface):

        def __init__(self, channel: CChannel, flasher: Flasher, **kwargs):
            """Initialize Auxiliary attributes.
            Any auxiliary must at least be initialised with a CChannel.
            If needed, a Flasher can also be attached.
            Any additional parameter can be added depending on the implementation.
            The additional kwargs contain the auxiliarie's alias and logger
            names to keep activated, all defined in the configuration file.
            """
            super().__init__(**kwargs)
            self.channel = channel
            self.flasher = flasher

        def _create_auxiliary_instance(self):
            """Create the auxiliary instance at test setup.
            This method is also called when running self.resume()
            Simply flash the device under test with the attached Flasher instance
            and open the communication with the attached CChannel instance.
            """
            logging.info("Flash target")
            # used as context manager to close the flashing HW (debugger)
            # after successful flash
            with self.flash as flasher:
                flasher.flash()
            logging.info("Open communication")
            self.channel.open()

        def _delete_auxiliary_instance(self):
            """Delete the auxiliary instance at test teardown.
            This method is also called when running self.suspend()
            Simply end the communication by closing the attached CChannel instance.
            """
            logging.info("Close communication")
            self.channel.close()

        def send(self, to_send):
            """Send data without waiting for any response."""
            # self._run_command(("command", "send", to_send)) will be called internally
            return self.run_command("send", to_send, timeout_in_s=0)

        def send_raw_bytes(self, to_send):
            """Send raw data without waiting for any response."""
            # self._run_command(("command", "send", to_send)) will be called internally
            return self.run_command("send raw", to_send, timeout_in_s=0)

        def send_and_wait_for_response(self, to_send, timeout = 1):
            """Send data and wait for a response during `timeout` seconds."""
            # returns True if the command was successfully executed
            command_sent = self.run_command("send", to_send, timeout_in_s=0)
            if command_sent:
                # method of AuxiliaryCommon that tries to get an element from queue_out
                # queue_out is populated by self._receive_message()
                return self.wait_and_get_report(timeout_in_s=timeout)

        def _run_command(self, cmd_message, cmd_data):
            """Command execution method that is called internally by the
            AuxiliaryInterface Thread.
            Each public API method should call this method with a command message
            and the data corresponding to the command.
            The command message is then matched against every possible implemented
            message and the corresponding action is performed in a thread-safe way.
            In this example, only a "send" command is implemented that will simply
            send the command data over the attached communication channel.
            """
            if cmd_message == "send":
                # in the CChannel implementation raw is set to False by default
                # the data to send is then pre-serialized according to the specified protocol
                return self.channel.send(cmd_data)
            elif cmd_message == "send raw":
                # set raw to True to send raw bytes through the CChannel
                return self.channel.send(cmd_data, raw=True)

        def _receive_message(self, timeout_in_s):
            """Reception method that is called internally by the AuxiliaryInterface Thread.
            Verify if there is 'raw' data to receive for 10ms and return it.
            """
            try:
                received_data = self.channel.cc_receive(timeout=timeout_in_s, raw=True)
                if received_data is not None:
                    return received_data
            except Exception:
                logging.exception(f"Channel {self.channel} failed to receive data")

Regarding a concrete implementation using :py:class:`~pykiso.auxiliary.AuxiliaryInterface`
take a look to :py:class:`~pykiso.lib.auxiliaries.communication_auxiliary.CommunicationAuxiliary` source code.

More examples are available under :py:mod:`pykiso.lib.auxiliaries`.

.. _aux_without_connector:

Auxiliary without connector
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If by default all auxiliaries require a connector, in some specific cases,
it may complicate the total implementation. Therefore `connector_required`
parameter was defined.

.. note::
    Auxiliaries that should fall into this category will need to be discussed
    case by case.

.. warning::
    Auxiliaries entering this category will raise an error if a connector is indeed
    assigned to it in the .yaml. Hybrid cases do not exist.

See below an example of an auxiliary without connector:

.. code:: python

  class ExampleAuxiliary(AuxiliaryInterface):
    """Example auxiliary without a connector"""

    def __init__(self) -> None:
      """Initialize the auxiliary"""
      super().__init__(connector_required=False)


See below for an example of its yaml config file:

.. code:: yaml

  auxiliaries:
    aux1:
      config: null
      type: pykiso.lib.auxiliaries.example_auxiliary:ExampleAuxiliary

  test_suite_list:
  - suite_dir: test_suite_1
    test_filter_pattern: '*.py'
    test_suite_id: 1
