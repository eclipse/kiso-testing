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

**Green-field** - Contribution of a new module
#. In `src/pykiso/lib/incubation` are two folders, one dedicated for the incubation of `auxiliaries` and the other for `connectors`.
  #. Depending on the type of module you want to contribute (:ref:`_how_to_create_connector` or :ref:`_how_to_create_aux`), create a module in the right folder.
#. Do not forget the unittests (same location of all unittests).
#. Do not forget to add your module to the documentation. Also add a `warning` section to inform the user that this module is in incubation phase.
#. Do not forget to add an usage example for your module.

**Gray-field** - Refactoring of an existing module
#. In `src/pykiso/lib/incubation` are two folders, one dedicated for the incubation of `auxiliaries` and the other for `connectors`.
#. Copy the module to refactor to the right folder.
#. Break, update the APIs, refactor it.
#. In the old location, if possible, inherit from it and replace the content of the legacy APIs. There should be no breaking changes,
   this step is to support backward compatibility.
#. In the documentation, extend the already existing .rst file with a warning specifying which APIs are in `incubation` / refactored and which one will be `deprecated`
   and removed in the next major release.
#. Extend the unittests to test the refactored APIs. Old tests should not be touched, they ensure the backward compatibility.
#. Do not forget the warning.
#. Users can access the new functionalities with from ebplugins.incubation.emb_aux the APIs with breaking changes.
#. Update the examples to use the new API.


Communication
-------------

Like for any other changes, we will be using `conventional commits <https://www.conventionalcommits.org/en/v1.0.0/>`_.

When a major release is planned, the breaking-changes will be communicated over the changelog.



ref: https://www.sebastianpfischer.com/index.php/2023/02/21/how-to-deal-with-breaking-changes-python/
