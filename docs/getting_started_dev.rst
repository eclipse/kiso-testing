Getting Started with pykiso for contributors
============================================


Requirements
------------

-  Python 3.6+
-  pipenv (used to get the rest of the requirements)

Install
-------

.. code:: bash

   git clone https://github.com/dbuehler85/pykiso.git
   cd pykiso
   pipenv install --dev
   pipenv shell

Pre-Commit
~~~~~~~~~~

To improve code-quality, a configuration of
`pre-commit <https://pre-commit.com/>`__ hooks are available. The
following pre-commit hooks are used:

-  black
-  trailing-whitespace
-  end-of-file-fixer
-  check-docstring-first
-  check-json
-  check-added-large-files
-  check-yaml
-  debug-statements

If you don’t have pre-commit installed, you can get it using pip:

.. code:: bash

   pip install pre-commit

Start using the hooks with

.. code:: bash

   pre-commit install

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

Building the Docs
~~~~~~~~~~~~~~~~~

.. code:: bash

    invoke docs
