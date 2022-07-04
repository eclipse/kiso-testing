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
auxiliary interface

CCProxy channel adaption
^^^^^^^^^^^^^^^^^^^^^^^^
Add thread-safe callback subscription mechanism to fit with the brand new
double threaded auxiliary interface

Communication Auxiliary adaption
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
refactor code of the communication auxiliary to fit with the brand new double
threaded auxiliary interface
