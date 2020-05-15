Getting Started with pykiso
===========================


Requirements
------------

-  Python 3.6+
-  pip/pipenv (used to get the rest of the requirements)

Install
-------

.. code:: bash

   git clone https://github.com/dbuehler85/pykiso.git
   cd pykiso
   pip install .

`Pipenv <https://github.com/pypa/pipenv>`__ is more appropriate for
developers as it automatically creates virtual environments.

.. code:: bash

   git clone https://github.com/dbuehler85/pykiso.git
   cd pykiso
   pipenv install --dev
   pipenv shell

Usage
-----

Once installed the application is bound to ``pykiso``, it can be called
with the following arguments:


.. command-output:: pykiso --help


Suitable config files are available in the ``test-examples`` folder.

Demo using example config
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   invoke run

Running the Tests
~~~~~~~~~~~~~~~~~

.. code:: bash

   invoke test

or

.. code:: bash

   pytest

List of limitations / todos for the python side
-----------------------------------------------

-  ☐ **When the auxiliary does not answer (ping or else),
   BasicTest.cleanup_and_skip() call will result in a lock
   and break the framework.**
-  ☐ No test-setion will be executed, needs to be removed later.
-  ☒ test configuration files need to be reworked
-  ☒ Names & configurations in the *cfg file json* are character precise
   class names & associated parameters.
-  ☐ Spelling mistakes need to be fixed! *ongoing*
-  ☐ Add verbosity parameters to pass to the unittest framework to get
   more details about the test.
-  ☐ **Add result parsing for Jenkins (see:
   https://stackoverflow.com/questions/11241781/python-unittests-in-jenkins).**
-  ☒ Create a python package
   -  ☐ and host it on pip.
