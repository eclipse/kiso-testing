User Guide
==========


Requirements
------------

-  Python 3.6+
-  pip/pipenv (used to get the rest of the requirements)

.. _pykiso_installation:

Install
-------

.. code:: bash

   git clone https://dev-bosch.com/bitbucket/scm/pea/integration-test-framework.git
   cd integration-test-framework
   pip install .

`Pipenv <https://github.com/pypa/pipenv>`__ is more appropriate for
developers as it automatically creates virtual environments.

.. code:: bash

   git clone https://dev-bosch.com/bitbucket/scm/pea/integration-test-framework.git
   cd integration-test-framework
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
