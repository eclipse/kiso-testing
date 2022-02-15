.. _how_to_create_aux:

How to create an auxiliary
==========================

This tutorial aims to explain the working principle of an Auxiliary by
providing information on the different Auxiliary interfaces, their purpose
and the implementation of new auxiliaries.

To provide hints on the implementation of an Auxiliary, an example that
implements a generic auxiliary is provided, that is not usable but shall
explain the different concepts and implementation steps.

Different Auxiliary interfaces for different use-cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pykiso provides three different auxiliary interfaces, used as basis for
any implemented auxiliary. These different interfaces aim to cover every
possible usage of an auxiliary:

- The :py:class:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`
  is a `Thread <https://docs.python.org/3.7/library/threading.html#threading.Thread>`_-based auxiliary.
  It is suited for IO-bound tasks where the reception of data cannot be expected.
- The :py:class:`~pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`
  is a `Process <https://docs.python.org/3.7/library/multiprocessing.html#multiprocessing.Process>`_-based auxiliary.
  It is suited for CPU-bound tasks where the reception of data cannot be expected and its processing can be CPU-intensive.
  In contrary to the Thread-based auxiliary, this interface is not limited by the GIL and runs on all available CPU cores.
- The :py:class:`~pykiso.interfaces.simple_auxiliary.SimpleAuxiliaryInterface`
  does not implement any kind of concurrent execution. It is suited for host-based applications where the auxiliary
  initiates every possible action, i.e. the reception of data can always be expected.

Execution of an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~~~~

Auxiliary creation and deletion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any auxiliary is **created** at test setup (before any test case is executed) by calling :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.create_instance`
and **deleted** at test teardown (after all test cases have been executed) by calling :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.delete_instance`.

These methods set the :py:attr:`is_instance attribute <pykiso.auxiliary.AuxiliaryCommon.is_instance>` that
indicated if the auxiliary is running correctly.

Concurrent auxiliary execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The execution of concurrent auxiliaries (i.e. inheriting from :py:class:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`
or :py:class:`~pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`) is
handled by the interfaces' :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run>` method.

Each command execution is handled in a thread-safe way by getting values from an input queue and
returning the command result in an output queue.

Auxiliary run
^^^^^^^^^^^^^

Each time the execution is entered, the following actions are performed:

1. Verify if a request is available in the input queue

  #. If the command message is "create_auxiliary_instance" and the auxiliary is not created yet,
     call the :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._create_auxiliary_instance`
     method and put a boolean corresponding to the success of the command processing in the output queue.
     This command message is put in the queue at test setup.

  #. If the command message is "delete_auxiliary_instance" and the auxiliary is created, call
     the :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._delete_auxiliary_instance`
     method and put a boolean corresponding the success of the command processing in the output queue.
     This command message is put in the queue at test teardown.

  #. If the command message is a tuple of 3 elements starting with "command", then a custom command has to
     be executed. This custom command has to be implemented in the :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._run_command` method.

  #. If the command message is "abort" and the auxiliary is created, call the :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._abort_command`
     method and put a boolean corresponding the success of the command processing in the output queue.

2. Verify if a Message is available for reception

  #. Call the auxiliarie's :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._receive_message` method
  #. If something is returned, put it in the output queue, otherwise repeat this execution cycle.

Implement an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~

Common auxiliary methods
^^^^^^^^^^^^^^^^^^^^^^^^

All of the above described Auxiliary interfaces require the same abstract methods
to be implemented:

- :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._create_auxiliary_instance`:
  handle the auxiliary creation. Minimal actions to perform are
  opening the attached :py:class:`~pykiso.connector.CChannel`, to which can be added actions such as flashing the device under test,
  perform security related operations to allow the communication, etc.
- :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._delete_auxiliary_instance`:
  handle the auxiliary deletion. This method is the counterpart of
  ``_create_auxiliary_instance``, so it needs to be implemented in a way that ``_create_auxiliary_instance``
  can be called again without side effects. In the most basic case, it should at least close the opened :py:class:`~pykiso.connector.CChannel`.

Concurrent auxiliary methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to the previously described methods, the concurrent Auxiliary
interfaces :py:class:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`
and :py:class:`~pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface` require
the following methods to be implemented:

- :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._run_command`: implement the different commands that should be performed by the Auxiliary.
  The public API methods of an auxiliary should always call the thread-safe :py:meth:`~pykiso.auxiliary.AuxiliaryCommon.run_command`
  method with arguments corresponding to the command to run, which will in turn call this private method.
- :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._abort_command`: implement the command abortion mechanism. This mechanism **must also be implemented
  on the target device**. A valid implementation for the TestApp protocol can be found in
  :py:meth:`pykiso.lib.auxiliaries.dut_auxiliary.DUTAuxiliary._abort_command`.
- :py:meth:`~pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._receive_message`: implement the reception of data. This method should at least call the CChannel's
  :py:meth:`~pykiso.connector.CChannel.cc_receive` method. The received data can then be decoded according to a particular protocol, matched
  against a previously sent request, or trigger any kind of further processing.


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

        def _abort_command(self):
            """Command abortion method that is called by the AuxiliaryInterface Thread
            when calling `my_aux.abort_command()`.

            Assume that the device under test aborts the running command when receiving
            the data b'abort'.

            For the sake of simplicity, no further check will be performed on the successful
            reception of the data by the DUT (e.g. wait for an acknowledgement).
            """
            command_sent = self.send_raw_bytes(b'abort')
            return command_sent

        def _receive_message(self):
            """Reception method that is called internally by the AuxiliaryInterface Thread.

            Verify if there is 'raw' data to receive for 10ms and return it.
            """
            try:
                received_data = self.channel.cc_receive(timeout=0.01, raw=True)
                if received_data is not None:
                    return received_data
            except Exception:
                logging.exception(f"Channel {self.channel} failed to receive data")

More examples are available under :py:mod:`pykiso.lib.auxiliaries`.

.. note::
    If the created auxiliary should be based on multiprocessing instead
    of threading, only the base class needs to be changed from
    ``AuxiliaryInterface`` to ``MpAuxiliaryInterface``. The actual
    implementation does not need any adaptation.
