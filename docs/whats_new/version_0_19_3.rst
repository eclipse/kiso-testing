Version 0.19.3
--------------


Double Threaded Auxiliary Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Implement a brand new interface using two threads, one for the transmission
and one for the reception.

Adapted modules for this release:
- Proxy Auxiliary
- CCProxy channel
- Communication Auxiliary
- DUT Auxiliary
- Record Auxiliary
- Acroname Auxiliary
- Instrument Auxiliary
- UDS Auxiliary
- UDS server Auxiliary

There is not API changes, therefor, as user, your tests should not be affected.


Kiso log levels
^^^^^^^^^^^^^^^
To let users decide the level of information they want to see in their logs, new log levels
have been defined. When launched normally only the logs in the tests and the errors will be
active.
The option -v (--verbose) should be used to display the internal logs of the framework.

See :ref:`run_the_tests`


Filter for Test cases
^^^^^^^^^^^^^^^^^^^^^
It is now possible to select test classes or even test cases with a unix filename
pattern.
This pattern can be passed with the -p flag or inside the yaml file.

For more info see
:ref:`test_case_patterns`


Agnostic tag call
^^^^^^^^^^^^^^^^^
Instead of having only the 2 tags "variant" and "branch_level" to select tests, users
can now set any tagname.

See: :ref:`define_test_information` for more details.


Step report (better reports for system-tester)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
It tracks each assertion containing a message to create a comprehensive test-report.

See: :ref:`step_test` for more details.


Agnostic CCSocketCan
^^^^^^^^^^^^^^^^^^^^
Incompatibilities with the agnostic proxy are now resolved. You should be able to use it again.


Tester Present Sender
^^^^^^^^^^^^^^^^^^^^^
Add a context manager, tester present sender, that send cyclic tester present
frames to keep UDS session alive more than 5 seconds

It can also be started and stopped by using the following methods:
 `start_tester_present_sender()` and `stop_tester_present_sender()`.

See :ref:`start_stop_tester_present_sender`
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


Lightweight UDS auxiliary configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The add of an .ini file to configured the UDS auxiliary and it variant (server)
is no more mandatory, every parameter is now reachable in the .yaml file.

See :ref:`examples/uds.yaml`

In addition, if the tp_layer and uds_layer parameters are not given at yaml level
a default configuration is applied.

See :ref:`uds_auxiliary`


New serial connector
^^^^^^^^^^^^^^^^^^^^
Added cc_serial for serial communication.


Tool for test suites tags analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See :ref:`show_tag`
