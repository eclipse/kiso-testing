Dynamic Configuration
=====================

In some situation, it is useful to change the in-use auxiliary behavior dynamically.
For example, switching for a brand new channel or simply change an attribute value.

Thanks to the common auxiliary interface, user can easily change his auxiliary
configuration by simply stop it (call of delete_instance public method) ,access
it different public attributes, and then just restarts the auxiliary (call of
create_instance public method)

.. warning:: if you are using the original auxiliary instance don't forget to
    switch back to it initial configuration for the next test cases.

Find below a complete example where during the test, the current pcan
connector is replaced by a simple CCLoopback:

.. literalinclude:: ../../examples/templates/suite_proxy/test_proxy.py
    :language: python
    :lines: 22-152

.. warning:: this feature allows to change the complete auxiliary configuration,
	so depending on which parameters are changed the auxiliary execution could lead
	to unexpected behaviors.
