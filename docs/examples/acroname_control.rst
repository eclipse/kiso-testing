.. _acroname_aux:

Controlling an acroname USB hub
===============================

The acroname auxiliary offers commands to control an acroname usb hub.
Ports can be switched individually and their current and voltage can be measured.
It is also possible to retrieve and set the current limitation of each port.


Usage Examples
~~~~~~~~~~~~~~

To use the auxiliary in your test scripts the auxiliary must be properly defined
in the config yaml. Example:

.. code:: yaml

  auxiliaries:
      acro_aux:
        config:
          # Serial number to connect to. Example: "0x66F4859B"
          serial_number : null # null = auto detection.
        type: pykiso.lib.auxiliaries.acroname_auxiliary:AcronameAuxiliary

Below find a example for the usage in a test script. All available methods are shown there.
For convenience units can be selected via a string.
For current methods use 'uA', 'mA' or 'A'.
For voltage methods use 'uV', 'mV' or 'V'.
If not specified 'V' or 'A' will be used.

.. literalinclude:: ../../examples/test_suite_acroname/test_acroname.py
    :language: python
