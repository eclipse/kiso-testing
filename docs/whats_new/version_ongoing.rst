Version ongoing
---------------

Improved logging for multiple yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is now possible to use a separate log file for each YAML if multiple are
provided. A folder can also be passed in which case separate log files will
be created with the corresponding YAML name.

Improved Report name
^^^^^^^^^^^^^^^^^^^^

For trace ability the report name will now also include the name of the
used config file.

Entirely hidden Proxy Auxiliary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is now no need at all anymore to manually define a ``ProxyAuxiliary`` and
``CCProxy``s.

If ``auto_start`` is disabled for all auxiliaries sharing a communication channel,
then the ``ProxyAuxiliary`` won't be started and the shared communication channel
will remain closed.

Afterwards, the shared communication channel can be opened and closed by respectively
starting one of the auxiliaries and stopping all of the auxiliaries.

For more information, please refer to :ref:`sharing_a_cchan`.
