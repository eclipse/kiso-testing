How to integrate
----------------

To bind ITF with Robot framework, the RobotLoader library has to be used in order to correctly create
all auxiliaries and connectors (using the "usual" yaml configuration style). This step is mandatory, and
could be done using the "Library" keyword and RobotLoader install/uninstall function. For example, inside
a test suite using "Suite Setup" and "Suite Teardown":

.. code-block:: robotframework

   *** Settings ***
   Documentation   How to handle auxiliaries and connectors creation using Robot framework

   Library    pykiso.lib.robot_framework.loader.RobotLoader    robot_com_aux.yaml    WITH NAME    Loader

   Suite Setup       Loader.install
   Suite Teardown    Loader.uninstall
