Passively record a channel
==========================

The record auxiliary can be used to utilize the logging mechanism from a connector.
For example the realtime trace from the segger jlink can be recorded during
a test run.

Usage Examples
~~~~~~~~~~~~~~

To use the auxiliary in your test scripts the auxiliary must be properly defined
in the config yaml. Example:

.. literalinclude:: ../examples/record_rtt_segger.yaml
    :language: yaml

Below find a example for the usage in a test script. It is only necessary to
import record auxiliary.

.. code:: python

  from pykiso.auxiliaries import record_aux


Example test script:

.. literalinclude:: ../examples/test_record/test_record.py
    :language: python
