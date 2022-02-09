Make an auxiliary copy
======================

.. warning:: feature under development and testing. The copycat ability
	is not available for the multiprocessing/robot auxiliaries

In some situation, it is useful to create a copy of the in-use auxiliary.
This very special usecase is covered by methods create_copy and destroy_copy.

Those methods are part of the AuxiliaryCommon interface. Due to this
fact only threaded and multiprocessing auxiliaries are "copy capable".

By invoking the create_copy method, the "original" auxiliary will be
automatically suspended and a brand new one will be created. The only
difference between both is: the configuration.

The introduction of this copy capability allows the user to create a copycat
with a different configuration in order to have for specific test-cases, temporarily, the auxiliary to be defined differently than usually.
at a very specific testing time (during only one test case, setup, teardown...).
Thanks to the usage of python set, users only have to specify the parameters
they want to change.
This means, create_copy method will instanciate a brand new auxiliary based on
the input yaml configuration file and the user's desired changes.

.. warning:: create_copy only allows named parameters so don't forget to name it!!

To get the "original" auxiliary back, users have only to invoke the method
destroy_copy . This simply stops the current copied auxiliary and resumes
the original one.

.. warning:: this feature allows to change the complete auxiliary configuration,
	so depending on which parameters are changed the copied auxiliary could lead
	to unexpected behavior.

Please find below a complete example, where a original communication auxiliary
is copied and the copy is copied at it's turn.

.. literalinclude:: ../../examples/templates/suite_com/test_com.py
    :language: python
    :lines: 21-93

In case of a proxy setup please find below a concrete example :

.. literalinclude:: ../../examples/templates/suite_proxy/test_proxy.py
    :language: python
    :lines: 21-94
