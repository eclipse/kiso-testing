.. _zephyr_aux:

Interacting with a Zephyr test
==============================

The Zephyr auxiliary uses the Twister tool(https://docs.zephyrproject.org/latest/develop/test/twister.html) to execute Zephyr tests from a pykiso test.
A common use case is a pykiso test that interacts with a test on an embedded device via a communication interface.

Prerequisites
~~~~~~~~~~~~~
To use the Zephyr auxiliary, you need a working Zephyr environment where you can use the Twister tool to execute your testcases.
Refer to the Zephyr documentation for details: https://docs.zephyrproject.org/latest/develop/test/index.html

Usage Examples
~~~~~~~~~~~~~~

To use the auxiliary in your test scripts the auxiliary must be properly defined
in the config yaml:

.. code:: yaml

  auxiliaries:
    # Zephyr test auxiliary
    zephyr_aux:
      config:
        # Path to twister tool, will default to "twister"
        twister_path: twister
        # The location of the Zephyr test project
        test_directory: ./test_zephyr/zephyr_test_project
        # The name of the test in the test directory
        test_name: testing.ztest
        # Wait for test start on target when started
        wait_for_start: True
      type: pykiso.lib.auxiliaries.zephyr:ZephyrTestAuxiliary

Remarks:

- The test_directory contains the path of the directory that contains the testcase.yaml of the Zephyr test project.
- The test_name contains the test name that is listed in the testcase.yaml.

Then you can start the zephyr test from a test function or also setup/teardown, whatever you prefer:

.. literalinclude:: ../../examples/test_zephyr/test_zephyr.py
    :language: python
