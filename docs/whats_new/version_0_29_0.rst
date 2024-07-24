Version 0.29.0
--------------

Pykiso execution
^^^^^^^^^^^^^^^^

Should Pykiso terminate while some threads remain active, these threads will be forcibly shut down.
Any unresolved threads will be reported on stdout at the end.

CAN Auxiliary
^^^^^^^^^^^^^
The CanAuxiliary offer a context manager that can be used to collect all messages received while
the context manager is used.

PCAN Connector
^^^^^^^^^^^^^^

By default the CCPCanCan will create one trace file for all the test executed when the command `pykiso -c`
is executed.

The logging can be deactivated by passing the parameter `logging_activated` to False in the configuration of the connector.

The strategy for the creation of the trace file can also be modified to create trace file for every test run or
for every testCase run, by adding in the configuration of the CCPCanCan the parameter strategy_trc_file
that take two possible values : "testRun" or "testCase".
