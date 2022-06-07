Version 0.18.0
--------------

Remote approach for test
^^^^^^^^^^^^^^^^^^^^^^^^
Remove all that is remote specific from BasicTestXXXX.
The remote approach is now handle by RemoteTestXXXX.

Pykiso To Pytest
^^^^^^^^^^^^^^^^

See :ref:`pykiso_to_pytest`

UDS Server Auxiliary
^^^^^^^^^^^^^^^^^^^^

A UDS auxiliary acting as a server/ECU is now implemented.
It is based on user-defined callbacks that send a UDS response when
the defined request is received.

See :ref:`uds_server_auxiliary`
