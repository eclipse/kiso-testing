How to create an auxiliary
--------------------------

Auxiliary Workflow during test execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Different Auxiliary interfaces for different use-cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pykiso provides three different auxiliary interfaces, used as basis for
any implemented auxiliary. These different interfaces aim to cover every
possible usage of an auxiliary:

- The ``AuxiliaryInterface``(:py:class:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`)
  is a `Thread <https://docs.python.org/3.7/library/threading.html#threading.Thread>`_-based auxiliary.
  It is suited for IO-bound tasks where the reception of data cannot be expected.
- The ``MpAuxiliaryInterface``(:py:class:`pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`)
  is a `Process <https://docs.python.org/3.7/library/multiprocessing.html#multiprocessing.Process>`_-based auxiliary.
  It is suited for CPU-bound tasks where the reception of data cannot be expected and its processing can be CPU-intensive.
- The ``SimpleAuxiliaryInterface``(:py:class:`pykiso.interfaces.simple_auxiliary.SimpleAuxiliaryInterface`)
  does not implement any concurrent execution. It is suited for host-based applications where the auxiliary
  initiates every possible action, i.e. the reception of data can always be expected.

Execution of an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~~~~

The execution of concurrent auxiliaries (i.e. inheriting from ``AuxiliaryInterface`` or
``MpAuxiliaryInterface``) is handled by the interfaces' methods
``run``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface.run`).

Each command execution is handled in a thread-safe way by getting values from an input queue and
returning the command result in an output queue.

Each time the execution is entered, the following actions are performed:

#. Verify if a request is available in the input queue
  #. If the command message is "create_auxiliary_instance" and the auxiliary is not created yet, call
  ``_create_auxiliary_instance``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._create_auxiliary_instance`)
  and put a boolean corresponding the success of the command processing in the output queue
  #. If the command message is "delete_auxiliary_instance" and the auxiliary is created, call
  ``_delete_auxiliary_instance``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._delete_auxiliary_instance`)
  and put a boolean corresponding the success of the command processing in the output queue
  #. If the command message is a tuple with 3 elements starting with "command", then a custom command has to
  be executed. This custom command has to be implemented in the ``_run_command``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._run_command`)
  command.
  #. If the command message is "abort" and the auxiliary is created, call
  ``_abort_command``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._abort_command`)
  and put a boolean corresponding the success of the command processing in the output queue
#. Verify if a Message is available for reception
  #. Call the method ``_receive_message``(:py:meth:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface._receive_message`)
  #. If something is returned, put it in the output queue, otherwise repeat this execution cycle.

Implement an Auxiliary
~~~~~~~~~~~~~~~~~~~~~~

All of the above described Auxiliary interfaces require the same abstract methods
to be implemented:

- ``_create_auxiliary_instance``: handle the auxiliary creation. Minimal actions to perform are
  opening the attached ``CChannel``, to which can be added actions such as flashing the device under test,
  perform security related operations to allow the communication, etc.
- ``_delete_auxiliary_instance``: handle the auxiliary deletion. This method is the counterpart of
  ``_create_auxiliary_instance`` and should at least close the opened ``CChannel``.


Additionally, the concurrent Auxiliary interfaces ``AuxiliaryInterface``(:py:class:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`)
and ``MpAuxiliaryInterface``(:py:class:`pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`) require the following
methods to be implemented:

- ``_run_command``: implement the different commands that should be performed by the Auxiliary.
- ``_abort_command``
- ``_receive_message``: implement the reception of data. This method should at least call the CChannel's
  `cc_receive` method. The received data can then be decoded according to a particular protocol, matched
  against a previously sent request, and trigger any kind of further processing.


See below an example implementing the basic functionalities of a Thread Auxiliary:

.. code:: python

    import logging
    from pykiso import AuxiliaryInterface, MpAuxiliaryInterface, CChannel, Flasher

    class MyAuxiliary(AuxiliaryInterface):

        def __init__(
            self,
            name: str,
            channel: CChannel,
            flasher: Flasher,
            arg: int,
            kwarg = "default_value",
            **kwargs
        ):
            super().__init__(name=name, **kwargs)
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

        def send_and_wait_for_response(self, to_send, timeout = 1):
            """Send data and wait for a response during timeout seconds."""
            command_sent = self.run_command("send", to_send, timeout_in_s=0)
            # returns True if the command was successfully executed
            if command_sent:
                # method of AuxiliaryCommon that tries to get an element from queue_out
                return self.wait_and_get_report(timeout_in_s=timeout)

        def _run_command(self, cmd_message, cmd_data):
            """Command execution method that is called internally by the
            AuxiliaryInterface Thread.

            """
            if cmd_message == "send":
                return self.channel.send(cmd_data)

        def _abort_command(self):


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

More examples are available under ``pykiso.lib.auxiliaries``(:py:mod:`pykiso.lib.auxiliaries`).

.. note::
    If the created auxiliary should be based on multiprocessing instead
    of threading, only the base class needs to be changed from
    ``AuxiliaryInterface`` to ``MpAuxiliaryInterface``. The actual
    implementation does not need any adaptation.
