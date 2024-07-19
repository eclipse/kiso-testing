cc_pcan_can
===========

.. automodule:: pykiso.lib.connectors.cc_pcan_can
    :members:
    :private-members:

Trace file Strategy
-------------------

By default the CCPCanCan will create one trace file for all the test executed when the command `pykiso -c`
is executed.

The logging can deactivated by passing the parameter `logging_activated` to False in the configuration.

But the strategy for the creation of the trace file can be modified to create trace file for every test run or
for every testCase run, it can be modified in the configuration of the CCPCanCan with the parameter strategy_trc_file
by passing a str : "test" or "testCase"

.. code:: yaml

    connectors:
    can_channel:
        config:
        interface: "pcan"
        channel: "PCAN_USBBUS1"
        state: "ACTIVE"
        type: pykiso.lib.connectors.cc_pcan_can:CCPCanCan
        strategy_trc_file: "test"
