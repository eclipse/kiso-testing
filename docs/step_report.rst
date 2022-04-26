Step report
===========

The step report aims to track each assertion.
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

Usage Examples
~~~~~~~~~~~~~~

.. code:: python

    def setUp(self):
        # data to test
        device_on = True
        voltage = 3.8

        # assert
        self.assertTrue(device_on, msg="Check my device is ready")

        # assert fail but continue on error
        # test is set to failed if assertion does not succeed
        self.step_report_continue_on_error = True
        self.assertTrue(!device_on, msg="Some check")

        # assert with custom message
        # assert msg overwritten when step_report_message not null
        self.step_report_message = "Custom message"
        self.assertAlmostEqual(voltage, 4, delta=1, msg="Check voltage device")

        # additional data to include in the step-report
        self.step_report_header["Version_device"] = "2022-1234"

"self.step_report_header" allows you to store data data during test


How to generate
~~~~~~~~~~~~~~~

.. code:: bash

  pykiso -c my_config.yaml --junit --step-report

"--junit" is required in order to get more information during test
