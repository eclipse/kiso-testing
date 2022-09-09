Contribution Guide
==================

What should I do before I get started?
--------------------------------------

You need to go through few steps to get the ball rolling. But no worries,
it is pretty straightforward.

Accounts
--------

First of all, you need accounts for:

  - Github account, some of you might already have one.
    If not, you can go to github and register a free user account in 2 minutes.

.. note::
  If you are working for a company and the work you are going to contribute
  is in the name of the company, please register your account using company
  email address.

  - Eclipse account, since Kiso-testing is an Eclipse project
  (full name: Eclipse Kiso-testing),   you need an Eclipse account.
  Go to https://accounts.eclipse.org/user/register to register one for free.

After a successful registration, you need to hook up your github account with
Eclipse account. Login in Eclipse foundation website and go to ‘Edit My Profile’
where you can bind your github account information.

ECA signing
-----------

ECA stands for ‘Eclipse Contributor Agreement’, which is a prerequisite to
become a contributor. No paper work needed, go to
https://www.eclipse.org/legal/ECA.php , read it carefully and follow its
instruction to sign.

DCO signing
-----------

DCO stand for "Developer's Certificate of Origin", which you will encounter as
part of ECA signing process. It is highly recommended that you read it, while
you as a developer might overlook the legal consequences if the way you
contribute does not follow certain rules and regulations.

License
-------

License is one of the few first things people would think of, when they use
or develop an open source project. Eclipse Kiso is and will be developed under
the EPL v2.0 license from Eclipse foundation.
Of course this exclude 3rd party source code.

EPL v2.0 is available under https://www.eclipse.org/legal/epl-2.0/ .
You need read it carefully before using Kiso-testing or developing on
Kiso-testing and make sure that you understand your rights and obligations.

Any contributions to Kiso-testing project code base needs to be licensed under
EPL v2.0.

.. include:: getting_started_dev.rst

What should I do before committing ?
------------------------------------

PEP8-Compliancy
---------------

In order to maintain clear and user-friendly project, make sure that your
changes respect PEP8 standards. PEP8 is a guide that provides Python coding
conventions (naming, indentation,...).
Official document : https://peps.python.org/pep-0008/

To make sure your changes are PEP8 Compliant, different tools exist to help you
here:

    - linter (applicable on IDE) :
        show some warning directly on IDE.
    - pre-commit hook :
        hook scripts that lint the added code using
        flake8 and format it using black and isort.


Typography
----------

Most of the comments made during PR-Reviewing are about typography/misspelling
mistakes. An easy way to avoid these is by running
`codespell <https://pypi.org/project/codespell/>`_ on your written code.


Function type hinting
---------------------

In kiso-testing, every implemented function must have annotations for its
parameters and return types (type hints). This results in increased readability and
therefore in easier comprehension of the code for any reader.

    .. code:: python

        def some_fun(some_dict_param: dict, some_string_param: str) -> list:

    .. note:: As not every types are available in the builtins, or as it is
        important to precise inner type you might import some from collections
        module or typing

    .. code:: python

        from typing import List
        from collections import namedtuple

        def some_fun(
            some_int_list_param: List[int], some_imported_type_param: namedtuple
        ) -> list:


Unit Testing
------------

To ensure the correct behaviour of your code, add unit tests for every function
you implemented.A convenient and pythonic way to do this is this is
given by `pytest <https://docs.pytest.org/en/stable/>`_
Code coverage is measured with `codecov <https://docs.codecov.com/docs>`_. It
simply checks if the code coverage is not going lower than it was before changes.

Examples Adaptation
-------------------

To ensure proper integration of your changes into the existing features,
and demonstrate their usages, adapt the examples of modified module, and run
it locally.

Update Documentation
--------------------

Regarding documentation there are four main purposes that have to be fulfilled
before committing :

    - Documentation regarding the changes :
        Make sure that the documentation allow easy understanding of the new
        feature(s).This step mainly concern docstring (module, class, and function)
        as shown below, but you could also have to change .rst documentation if
        your changes concern general working principle of the ITF (e.g. cli)
        To ensure proper formatting of the documentation, run ``invoke docs``
        in the poetry environment.

    .. code:: python

        """
        name_of_the_module
        ******************

        :module: name_of_the_module
        :synopsis: short description of the module.

        Extended description of the module's functionnality,
        how it works, etc

        .. currentmodule:: name_of_the_module
        """

    .. code:: python

        class ClassName:
        """Short description of class"""

    .. code:: python

        def fun(param1, param2):
        """Short description of fun.

        More extended description of the function
        if needed.

        :param param1: short description of param1
        :param param2: short description of param2
        :raise exception1: short description of raised exception

        :return: short description of the return parameter
        """

    .. note:: Make also sure to do the type hinting for exceptions


    - What's new section:
        Add your changes into the what's new section, so user can stay updated of the
        brand new features.

    - Changelog: (automatically updated)
        Your commit needs to follow the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) pattern.
        Changelog is updated automatically with the commit message.

    - Documentation has to build properly.
