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
  It is suited for IO-bound tasks where the reception of data cannot be predicted.
- The ``MpAuxiliaryInterface``(:py:class:`pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`)
  is a `Process <https://docs.python.org/3.7/library/multiprocessing.html#multiprocessing.Process>`_-based auxiliary.
  It is suited for CPU-bound tasks where the reception of data cannot be predicted and its processing can be CPU-intensive.
- The ``SimpleAuxiliaryInterface``(:py:class:`pykiso.interfaces.simple_auxiliary.SimpleAuxiliaryInterface`)
  does not implement any concurrent execution.


Implement an auxiliary
~~~~~~~~~~~~~~~~~~~~~~

All of the above described Auxiliary interfaces require the same abstract methods
to be implemented:

- ``_create_auxiliary_instance``: handle the auxiliary creation. Minimal actions to perform are
  opening the attached ``CChannel``, to which can be added actions
- ``_delete_auxiliary_instance``: handle the auxiliary deletion. This method is the counterpart of
  ``_create_auxiliary_instance`` and should at least close the opened ``CChannel``.


Additionally, the concurrent Auxiliary interfaces ``AuxiliaryInterface``(:py:class:`pykiso.interfaces.thread_auxiliary.AuxiliaryInterface`)
and ``MpAuxiliaryInterface``(:py:class:`pykiso.interfaces.mp_auxiliary.MpAuxiliaryInterface`) require the following
methods to be implemented:

- ``_run_command``
- ``_abort_command``
- ``_receive_message``


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

            Simply flash the device under test with the attached Flasher instance
            and open the communication with the attached CChannel instance.
            """
            logging.info("Close communication")
            self.channel.close()

        def _run_command(self, cmd_message, cmd_data):


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


.. note::
    If the created auxiliary should be based on multiprocessing instead
    of threading, only the base class needs to be changed from
    ``AuxiliaryInterface`` to ``MpAuxiliaryInterface``. The actual
    implementation does not need any adaptation.
