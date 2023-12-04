Version 0.26.0
--------------

Junit Report
^^^^^^^^^^^^

Custom path for the xml report can now be set.

Example:

pykiso -c config.yaml --junit=./reports/custom_report.xml


UDS auxiliary
^^^^^^^^^^^^^

New pykiso-python-uds now supports uds on classic CAN.
Just set `is_fd: False` inside the can connectors config.
