Pykiso Design
=============

Introduction
------------

Integration Test Framework (Pykiso) is a framework that can be used for both
white-box and black-box testing as well as in the integration and system
testing.

Quality Goals
-------------
The framework tries to achieve the following quality goals:

+---------------------------+----------------------------------------------------------------------------------------------------+
| Quality Goal (with prio)  | Scenarios                                                                                          |
+===========================+====================================================================================================+
| **Portability**           | The framework shall run on linux, windows, macOS                                                   |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall run on a raspberryPI or a regular laptop                                       |
+---------------------------+----------------------------------------------------------------------------------------------------+
| **Modularity**            | The framework shall allow me to implement complex logic and to run it over any communication port  |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall allow me to add any communication port                                         |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall allow me to use private modules within my tests if it respects its APIs        |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall allow me to define my own test approach                                        |
+---------------------------+----------------------------------------------------------------------------------------------------+
| **Correctness**           | The framework shall verify that its inputs (test-setup) are correct before performing any test     |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall execute the provided tests always in the same order                            |
+---------------------------+----------------------------------------------------------------------------------------------------+
| **Usability**             | The framework shall feel familiar for embedded developers                                          |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall feel familiar for system tester                                                |
+---------------------------+----------------------------------------------------------------------------------------------------+
|                           | The framework shall generate test reports that are human and machine readable                      |
+---------------------------+----------------------------------------------------------------------------------------------------+
| **Performance** (new)     | The framework shall use only the right/reasonable amount of resources to run (real-time timings)   |
+---------------------------+----------------------------------------------------------------------------------------------------+


Design Overview
---------------

.. figure:: ../images/pykiso_context_overview.png
   :alt: Figure 1: Integration Test Framework Context

   Figure 1: Integration Test Framework Context

The *pykiso* Testing Framework is built in a modular and configurable
way with abstractions both for entities (e.g. a handler for the device
under test) and communication (e.g. UART or TCP/IP).

The tests leverage the python *unittest*-Framework which has a similar
flavor as many available major unit testing frameworks and thus comes
with an ecosystem of tools and utilities.

Test Coordinator
~~~~~~~~~~~~~~~~

The **test-coordinator** is the central module setting up and running
the tests. Based on a configuration file (in YAML), it does the
following:

-  instantiate the selected connectors
-  instantiate the selected auxiliaries
-  provide the auxiliaries with the matching connectors
-  generate the list of tests to perform
-  provide the testcases with the auxiliaries they need
-  verify if the tests can be performed
-  for remote tests (see :ref:`remote_test`) flash and run and synchronize the tests on the auxiliaries
-  gather the reports and publish the results

Auxiliary
~~~~~~~~~

The **auxiliary** provides to the **test-coordinator** an interface to
interact with the physical or digital auxiliary target. It is composed
by 2 blocks:

-  instance creation / deletion
-  connectors to facilitate interaction and communication with the
   device (e.g. messaging with *UART*)

For example auxiliaries like the one interacting with cloud services,
we may have:

-  A communication channel (**cchannel**) like *REST*

Create an Auxiliary
^^^^^^^^^^^^^^^^^^^
Detailed information can be found here :ref:`how_to_create_aux`.

Connector
~~~~~~~~~

Communication Channel
^^^^^^^^^^^^^^^^^^^^^

The Communication Channel - also known as **cchannel** - is the medium
to communicate with auxiliary target. Example include *UART*, *UDP*,
*USB*, *REST*,… The communication protocol itself can be auxiliary
specific.

Create a Connector
^^^^^^^^^^^^^^^^^^
Detailed information can be found here :ref:`how_to_create_connector`.

Dynamic Import Linking
~~~~~~~~~~~~~~~~~~~~~~

The `pykiso` framework was developed with modularity and reusability in mind.
To avoid close coupling between testcases and auxiliaries as well as between auxiliaries and connectors, the linking between those components is defined in a config file (see :ref:`config_file`) and performed by the `TestCoordinator`.

Different instances of connectors and auxiliaries are given *aliases* which identify them within the test session.

Let's say we have this (abridged) config file:

.. code:: yaml

    connectors:
      my_chan:           # Alias of the connector
        type: ...
    auxiliaries:
      my_aux:            # Alias of the auxiliary
        connectors:
            com: my_chan # Reference to the connector
        type: ...

The auxiliary `my_aux` will automatically be initialised with `my_chan` as its `com` channel.

When writing your testcases, the auxiliary will then be available under its defined alias.

.. code:: python

    from pykiso.auxiliaries import my_aux

The ``pykiso.auxiliaries`` is a magic package that only exists in the ``pykiso`` package after the ``TestCoordinator`` has processed the config file.
It will include all *instances* of the defined auxiliares, available at their defined alias.

Usage
-----

Please see :ref:`config_file` to have a deep-dive on how the pykiso configuration work.

Please see :ref:`How to make the most of the tests` to have a deep-dive on how pykiso tests work.
