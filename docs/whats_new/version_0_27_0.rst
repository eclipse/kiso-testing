Version 0.27.x
--------------

Adding contextual test execution information to the JUnit report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any information can now be added to the test case section of the generated JUnit report
as JUnit properties.

For more information please refer to :ref:`junit_report`.


Add Virtual CAN Connector
^^^^^^^^^^^^^^^^^^^^^^^^^

Add new Virtual CAN connector that uses the UDP multicast interface from python-can


CAN auxiliary
^^^^^^^^^^^^^

Introducing the new CAN auxiliary! Now you can effortlessly send and receive CAN signals defined in a dbc file.

PCAN Connector
^^^^^^^^^^^^^^

Merging trc logs into one file can now be turned off by setting the
``merge_trc_logs`` parameter to ``False`` in the PCAN connector.

Pytest plugin
^^^^^^^^^^^^^

The ``pytest_kiso`` plugin is now compatible with ``pytest >= 8.1.0``.
