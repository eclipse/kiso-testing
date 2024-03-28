.. _api_lifecycle:

API Lifecycle
=============

To ensure a set of stable APIs, we introduced an API lifecycle.
This will allow us to introduce/incubate new features while keeping
the stable one up and running.

Principle to work for
---------------------

If we extend our existing functionalities while following the
`open-closed <https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle>`_
principle, there should not be any breaking changes visible to our users.

But as you all know, it is not that simple. Ensuring backward compatibilities is
directly impacting **maintainability** in the following ways:

* code we do not delete needs to be maintained (unittests and doc included)
* legacy APIs may include switch cases in new APIs
* legacy APIs may include dependencies to classes or modules we do not need


Different use-cases
-------------------

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Use-case
     - User expectations
     - Size of the complexity
   * - Refinement of a functionality
     - stable APIs
     - medium
   * - Refactoring activities of a functionality
     - stable APIs
     - medium
   * - Incubation of a new functionality
     - unstable APIs
     - big

API States
----------

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - State
     - Description
   * - stable
     - The API is stable and will not change in the future
   * - incubation
     - The API is not stable and may change in the future
   * - deprecated
     - The API is not recommended for use and may be removed in the future
   * - removed
     - The API is removed and no longer available

Approach
--------

#. Create an incubation folder in the repo
  #. The incubation should reflect the same skeleton as the main repository structure
#. Copy there the module that will create a breaking change or create there the module that will contain the new functionalities
#. Implement it, refactor it
#. In the old location, inherit from it and reimplement the APIs to not break the module
#. Do not forget the warning
#. Users can access the new functionalities with from ebplugins.incubation.emb_aux the APIs with breaking changes
#. Do not forget to update:
  #. The documentation
    #. Is it somehow possible in the API doc to have only one module shown?
    #. This way we could see what is the API that is deprecated but also the new API that replaces it
  #. The information about how to migrate to the new API
  #. The old module or function with a deprecation warning
    #. In the module that will contain the breaking change
  #. Unittests
    #. Implement the new unittests
    #. Do not touch the old one (to ensure that the functionality still behave as expected)
  #. Remark: if the unittest was badly written, it can be updated
  #. Examples
    #. Update the examples to use the new API


Communication
-------------

Like for any other changes, we will be using `conventional commits <https://www.conventionalcommits.org/en/v1.0.0/>`_.



ref: https://www.sebastianpfischer.com/index.php/2023/02/21/how-to-deal-with-breaking-changes-python/
