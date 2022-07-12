Version ongoing
---------------

WARNING
^^^^^^^
pykiso_to_pytest will generate none working contest.py until ticket `fix pykiso to pytest <https://github.com/eclipse/kiso-testing/issues/76>`__  is merged and finished.


Tool for test suites tags analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See :ref:`show_tag`

Double Threaded Auxiliary Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Implement a brand new interface using two threads, one for the transmission
and one for the reception.

Currently adapted modules:
- Proxy Auxiliary
- CCProxy channel
- Communication Auxiliary
- DUT Auxiliary
- Record Auxiliary
- Acroname Auxiliary

There is not API changes, therefor, as user, your tests should not be affected.

Agnostic CCSocketCan
^^^^^^^^^^^^^^^^^^^^
Incompatibilities with the agnostic proxy are now resolved. You should be able to use it again.

Tester Present Sender
^^^^^^^^^^^^^^^^^^^^^
Add a context manager, tester present sender, to keep a UDS session open for
more than 5 seconds
See :ref:`uds_auxiliary`
