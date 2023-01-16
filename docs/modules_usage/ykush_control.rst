.. _ykush_aux:

Controlling an Yepkit USB hub
===============================

The ykush auxiliary offers commands to control an Yepkit USB hub,
allowing to switch the USB ports on and off individually.


Usage Examples
~~~~~~~~~~~~~~

To use the auxiliary in your test scripts the auxiliary must be properly defined
in the config yaml. Example:

.. code:: yaml

  auxiliaries:
      ykush_aux:
        config:
          # Serial number to connect to. Example: "YK00006"
          serial_number : null # null = auto detection.
        type: pykiso.lib.auxiliaries.ykush_auxiliary:YkushAuxiliary

Below find a example for the usage in a test script. All available methods are shown there.

.. literalinclude:: ../../examples/test_suite_ykush/test_ykush.py
    :language: python
