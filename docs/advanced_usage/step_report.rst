.. _step_test:

System-test (step) report
=========================

The step report aims to provide a more comprehensive test-report (adapted for system testers) by tracking each assertion that contains a message.
It follows the following structure:

- test name
- test description
- date of execution
- elapsed time
- information gathered during test
- assertion detail:
  - value of the data_in
  - variable name of the data_in
  - expected value
  - message
- the report is presented as an HTML page

Usage Examples
~~~~~~~~~~~~~~

.. code:: python

    def setUp(self):
        # Data to test
        device_on = True
        voltage = 3.8

        # Simple assert
        self.assertTrue(device_on, msg="Check my device is ready")

        with self.subTest("Non critical checks"):
            # This check will fail but the test continues
            self.assertFalse(device_on, msg="Some check")

        # Add a new table in the report
        self.step_report.current_table = "Another table"

        # Assert with custom message
        # Assert msg overwritten when step_report_message not null
        self.step_report.message = "Custom message"
        self.assertAlmostEqual(voltage, 4, delta=1, msg="Check voltage device")

        # Additional data to include in the step-report
        self.step_report.header["Version_device"] = "2022-1234"

"self.step_report.header" allows you to store data data during test


How to generate
~~~~~~~~~~~~~~~

.. code:: bash

  pykiso -c my_config.yaml --step-report my_report.html

Limitations
~~~~~~~~~~~
The step report generator might fail if you put parentheses or "assert" strings in strings or comments in the assert statement.

HTML result example
~~~~~~~~~~~~~~~~~~~
.. image:: step_report.png
