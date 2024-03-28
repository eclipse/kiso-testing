Version 0.28.0
--------------

Communication Auxiliary
^^^^^^^^^^^^^^^^^^^^^^^

Receive method of the Communication Auxiliary can now also return the message timestamp
if the corresponding parameter is set to True.

PCAN Connector
^^^^^^^^^^^^^^

Trace file can be stopped and started by the function ``stop_pcan_trace`` and ``start_pcan_trace``
to create logfiles on the fly.
