Version ongoing
---------------

WARNING
^^^^^^^
pykiso_to_pytest will generate none working contest.py until ticket `fix pykiso to pytest <https://github.com/eclipse/kiso-testing/issues/76>`__  is merged and finished.


Tool for test suites tags analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See :ref:`show_tag`

Double Threaded Auxiliary Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Implement a brand new interface using two threads, one for the transmission
and one for the reception.

Currently adapted modules:
- Proxy Auxiliary
- CCProxy channel
- Communication Auxiliary
- DUT Auxiliary
- Record Auxiliary
- Acroname Auxiliary

There is not API changes, therefor, as user, your tests should not be affected.

Agnostic CCSocketCan
^^^^^^^^^^^^^^^^^^^^
Incompatibilities with the agnostic proxy are now resolved. You should be able to use it again.

Tester Present Sender
^^^^^^^^^^^^^^^^^^^^^
Add a context manager, tester present sender, that send cyclic tester present
frames to keep UDS session alive more than 5 seconds

See :ref:`uds_auxiliary`

RTT connector log folder creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RTT connector now creates a log folder if it does not exist instead of throwing an error.

Communication Auxiliary
^^^^^^^^^^^^^^^^^^^^^^^
To save on memory, the communication auxiliary does not collect received messages automatically anymore.
The functionality is now available with the context manager ``collect_messages``.

See :ref:`examples/templates/suite_com/test_com.py`

The collected messages by the Communication auxiliary can still be cleared with the API method
:py:meth`~pykiso.lib.auxiliaries.communication_auxiliary.CommunicationAuxiliary.clear_buffer`

See :ref:`communication_auxiliary`

Configurable waiting for send_uds_raw
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To avoid extra waiting time during long/heavy UDS data exchange(flashing) expose
the parameter tpWaitTime from kiso-testing-python-uds for uds auxilary send_uds_raw
method

See :ref:`uds_auxiliary`
