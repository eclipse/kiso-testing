Version 0.21.1
--------------

Remove redundancy of activate_log configuration parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to activate external loggers, it was previously necessary to
specify their names for each defined auxiliary.

This is no longer the case and specifying them in only one auxiliary
will be enough for the loggers to stay enabled.


Internal creation of proxy auxiliaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is no longer necessary to manually define a ``ProxyAuxiliary`` with
``CCProxy`` instances yourself. If you simply pass the communication channel to
each auxiliary that has to share it, ``pykiso`` will do the rest for you.

For more information see :ref:`sharing_a_cchan`


Better skipping of test cases based on tags
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The test case filtering strategy based on the test tags has been reworked.
The resulting skipped test cases now appear explicitly as skiped in the test run output

For more information refer to :ref:`test_tags`


Ykush Auxiliary
^^^^^^^^^^^^^^^
Auxiliary that can be used to power on and off the ports of an Ykush USB Hub.

See :ref:`ykush_auxiliary`


Multiple auxiliaries can share a communication channel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

see :ref:`Sharing a communication channel between multiple auxiliaries`


Remove raw from connector functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The functions cc_receive and cc_send for every connector no longer take raw
as an argument.


Results can be exported on TestRail
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

see :ref:`testrail`


Step report
^^^^^^^^^^^

Tests are now foldable items.
