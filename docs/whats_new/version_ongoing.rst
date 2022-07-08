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

Proxy Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^^^
refactor code of the proxy auxiliary to fit with the brand new double threaded
auxiliary interface.
Add useful decorators for common behaviors open_connector, close_connector, flash_target.

CCProxy channel adaption
^^^^^^^^^^^^^^^^^^^^^^^^
Add thread-safe callback subscription mechanism to fit with the brand new
double threaded auxiliary interface

Communication Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
refactor code of the communication auxiliary to fit with the brand new double
threaded auxiliary interface

DUT Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^
refactor/redesign of the device under test auxiliary to fit with the brand new double
threaded auxiliary interface

Record Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^^^^
adapt the record auxiliary to fit with the brand new double threaded auxiliary interface

Acroname Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^^^^^^
adapt the acroname auxiliary to fit with the brand new double threaded auxiliary interface

Tester Present Sender
^^^^^^^^^^^^^^^^^^^^^
Add a context manager, tester present sender, to keep a UDS session open for
more than 5 seconds

