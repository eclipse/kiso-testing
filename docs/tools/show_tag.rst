
.. _show_tag:

Show and export test suite tags
===============================

The ``pykiso-tags`` CLI utility takes as input YAML configuration files and passively loads
all the specified test suites in order to create a test information table.

This table contains the number of test cases that will be run when providing this
configuration file to pykiso and the test tags that are specified in each test suite.

Another options can be specified and the table can be exported to various formats. See:

.. code:: bash

    pykiso-tags --help


A minimal invocation of the tool would be:

.. code:: bash

    pykiso-tags -c kiso-testing/examples/dummy.yaml


Which results in the following output:

.. code:: bash

    Start analyzing provided configuration file...

    All valid configuration files have been processed successfully:

    ╒═════════════╤═══════════════════╤═══════════╤════════════════╕
    │ File name   │   Number of tests │ variant   │ branch_level   │
    ╞═════════════╪═══════════════════╪═══════════╪════════════════╡
    │ dummy.yaml  │                 7 │ variant1  │ daily          │
    │             │                   │ variant3  │ nightly        │
    ╘═════════════╧═══════════════════╧═══════════╧════════════════╛

.. note::
    If an environment variable without a default value is not found,
    the tool will skip the configuration file.
    Also, configuration files for Robot framework tests are not
    supported yet.
