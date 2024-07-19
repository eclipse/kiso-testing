cc_pcan_can
===========

.. automodule:: pykiso.lib.connectors.cc_pcan_can
    :members:
    :private-members:

Trace file Strategy
-------------------

By default the CCPCanCan will create one trace file for all the test executed when the command `pykiso -c`
is executed.

The logging can be deactivated by passing the parameter `logging_activated` to False in the configuration of the connector.

The strategy for the creation of the trace file can also be modified to create trace file for every test run or
for every testCase run, by adding in the configuration of the CCPCanCan the parameter strategy_trc_file
that take two possible value : "test" or "testCase"

.. code:: yaml

    connectors:
    can_channel:
        config:
        interface: "pcan"
        channel: "PCAN_USBBUS1"
        state: "ACTIVE"
        type: pykiso.lib.connectors.cc_pcan_can:CCPCanCan
        strategy_trc_file: "test"
