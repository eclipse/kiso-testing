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

   pip install pykiso # Core framework
   pip install pykiso[plugins] # To install all plugins
   pip install pykiso[can] # To enable you to use CAN related plugins
   pip install pykiso[debugger] # To enable you to use JLINK and else related plugins
   pip install pykiso[instrument] # To enable you to use instrument control plugins

   pip install pykiso[all] # To enable you to install everything we have to offer

`Poetry <https://python-poetry.org/>`__ is more appropriate for
developers as it automatically creates virtual environments.

.. code:: bash

   git clone https://github.com/eclipse/kiso-testing.git
   cd kiso-testing
   poetry install --all-extras
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
