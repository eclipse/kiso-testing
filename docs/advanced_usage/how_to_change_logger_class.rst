.. _change_logger_class:


How to change the class of the logger
-------------------------------------

Change logger class
~~~~~~~~~~~~~~~~~~~

You can change the class of the loggers used in pykiso with a custom logger class.

For example you have created a logger class (TestLogger) in the package called package_test in a file called logger_test.
To use it you have pass the path to import the class as the value for --logger : package_test.test_logger.TestLogger

.. code:: bash

  pykiso -c my_config.yaml --logger package_test.test_logger.TestLogger

Class with argument
~~~~~~~~~~~~~~~~~~~

If you have created a logger class that takes more argument than name and level
to be initialized, you can specify them so that all loggers will be initialized
with the same value.

See the following example :

.. code:: python

   class TestLogger(logging.Logger):
        def __init__(
            self, name: str, str_arg: str, int_arg: int, level=0
        ) -> None:
            super().__init__(name, level)
            self.str_arg = str_arg
            self.int_arg = int_arg

.. code:: bash

  pykiso -c my_config.yaml --logger 'package_test.test_logger.TestLogger(str_arg=value,int_arg=12)'
