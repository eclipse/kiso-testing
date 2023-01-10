Version ongoing
---------------

Remove redundancy of activate_log configuration parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to activate external loggers, it was previously necessary to
specify their names for each defined auxiliary.

This is no longer the case and specifying them in only one auxiliary
will be enough for the loggers to stay enabled.
