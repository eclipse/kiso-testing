

Version 0.16.0
--------------

Global Config
^^^^^^^^^^^^^

Configuration paramertes can now be passed from the cli or the yaml file into your test.

See :ref:`global_config`


Fail Fast
^^^^^^^^^

With the new --fail-fast flag which can be passed through the pykiso cli,
tests will be stopped on the first error or failure.

At the same time the behavior of the auxiliary create instance was changed.
When the auxiliary instance creation are now failing, they will raise an exception.
Combined with the new flag the test execution will be stopp when something went wrong.


Include Sub-YAMLs
^^^^^^^^^^^^^^^^^

Frequently used configuration parts can be stored in a separate YAML file.

See :ref:`config_sub_yaml`
