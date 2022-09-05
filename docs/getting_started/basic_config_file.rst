.. _basic_config_file:


Basic configuration
-------------------

The test configuration files are written in YAML.

Let's use an example to understand the structure.

.. literalinclude:: ../../examples/dummy.yaml
    :language: yaml
    :linenos:

Connectors
~~~~~~~~~~

The connector definition is a named list (dictionary in python) of key-value pairs, namely config and type.

.. literalinclude:: ../../examples/dummy.yaml
    :language: yaml
    :lines: 12-21

The channel alias will identify this configuration for the auxiliaries.

The config can be omitted, `null`, or any number of key-value pairs.

The type consists of a module location and a class name that is expected to be found in the module.
The location can be a path to a python file (Win/Linux, relative/absolute) or a python module on the python path (e.h. `pykiso.lib.connectors.cc_uart`).

.. code:: yaml

    <chan>:                      # channel alias
        config:                  # channel config, optional
            <key>: <value>       # collection of key-value pairs, e.g. "port: 80"
        type: <module:Class>     # location of the python class that represents this channel


Auxiliaries
~~~~~~~~~~~

The auxiliary definition is a named list (dictionary in python) of key-value pairs, namely config, connectors and type.

.. literalinclude:: ../../examples/dummy.yaml
    :language: yaml
    :lines: 1-11


The auxiliary alias will identify this configuration for the testcases.
When running the tests the testcases can import an auxiliary instance defined here using

.. code:: python

    from pykiso.auxiliaries import <alias>

The connectors can be omitted, `null`, or any number of role-connector pairs.
The roles are defined in the auxiliary implementation, usual examples are `com` and `flash`.
The channel aliases are the ones you defined in the connectors section above.

The config can be omitted, `null`, or any number of key-value pairs.

The type consists of a module location and a class name that is expected to be found in the module.
The location can be a path to a python file (Win/Linux, relative/absolute) or a python module on the python path (e.h. `pykiso.lib.auxiliaries.communication_auxiliary`).

.. code:: yaml

    <aux>:                           # aux alias
        connectors:                  # list of connectors this auxiliary needs
            <role>: <channel-alias>  # <role> has to be the name defined in the Auxiliary class,
                                     #  <channel-alias> is the alias defined above
        config:                      # channel config, optional
            <key>: <value>           # collection of key-value pairs, e.g. "port: 80"
        type: <module:Class>         # location of the python class that represents this auxiliary


Test Suites
~~~~~~~~~~~

The test suite definition is a list of key-value pairs.

.. literalinclude:: ../../examples/dummy.yaml
    :language: yaml
    :lines: 22-34

Each test suite consists of a `test_suite_id`, a `suite_dir` and a `test_filter_pattern`.

For fast test development, the `test_filter_pattern` can be overwritten from the command line
in order to e.g. execute a single test file inside the `suite_dir` using the CLI argument `-p` or `--pattern`:

.. code:: bash

    pykiso -c dummy.yaml

To learn more, please take a look at :ref:`config_file`.
