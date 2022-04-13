User Guide
==========


Requirements
------------

-  Python 3.7+
-  pip

.. _pykiso_installation:

Install
-------

.. code:: bash

   pip install pykiso

`Poetry <https://python-poetry.org/>`__ is more appropriate for
developers as it automatically creates virtual environments.

.. code:: bash

   git clone https://github.com/eclipse/kiso-testing.git
   cd kiso-testing
   poetry install
   poetry shell

Usage
-----

Once installed the application is bound to ``pykiso``, it can be called
with the following arguments:


.. command-output:: pykiso --help


Suitable config files are available in the ``examples`` folder.

Demo using example config
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   pykiso -c ./examples/dummy.yaml --log-level=DEBUG -l killme.log
