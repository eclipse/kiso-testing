.. _global_config:

Access framework's configuration
--------------------------------

All parameters given at CLI and yaml level are available for each test cases/suites.
For a convenient usage, all configuration information are class based represented.
This means each parameter is accessible like a "normal" instance attribute (dot-access)
and the attribute's name is simply the one given in the yaml or the CLI level.

Each parameter stored in GlobalConfig's yaml and CLI attributes is read-only.

.. warning:: assign a new value will automatically raise an AttributeError

Let's admit we have the following yaml configuration file:

.. literalinclude:: ../examples/conf_access.yaml
    :language: yaml

And we passed the following arguments at the command line interface:

.. code:: bash

   pykiso -c examples/conf_access.yaml --variant variant1 --variant daily --log-level INFO

To access all those parameters contain in both sources (cli and yaml) :

.. literalinclude:: ../examples/conf_access/test_access.py
    :language: python

.. note:: the GlobalConfig class is a singleton, so one and only one instance
    is created during the whole execution time
