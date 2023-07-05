Version 0.23.0
--------------

New expand and collapse buttons for the StepReport
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Added buttons to expand or collapse all or all failed tests.

Pytest integration
^^^^^^^^^^^^^^^^^^

Pykiso test suites can now be run without any further change with ``pytest``.

For more information please refer to :ref:`pytest_integration`.

Connect to serial devices via pid/vid
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Added the possibility to connect to serial devices using pid and vid.

Timestamp in pykiso message dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Added the timestamp to the pykiso message dictionary for CAN dongles.

Add changeable logger class for the test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the possibility to change the logger class with the CLI.
For more information please refer to :ref:`change_logger_class`.

Add shutdown method to CCHannel 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add proper shutdown method for connector instead of instead of using
the del method
