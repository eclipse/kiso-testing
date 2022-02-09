cc_socket_can
=============

Setup SocketCAN
---------------

To use the socketCAN connector you have to make sure that your can socket has been
initialized correctly.

.. code-block:: bash

   sudo ip link set can0 up type can bitrate 500000 sample-point 0.75 dbitrate 2000000 dsample-point 0.8 fd on
   sudo ip link set up can0

Make sure that ifconfig shows a socket can interface.
Example shows can0 as available interface:

.. code-block:: bash

   ifconfig
   # outputs->
   can0: flags=193<UP,RUNNING,NOARP>  mtu 72
           unspec 00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00  txqueuelen 1000  (UNSPEC)
           RX packets 30  bytes 90 (90.0 B)
           RX errors 0  dropped 0  overruns 0  frame 0
           TX packets 30  bytes 90 (90.0 B)
           TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

.. warning::
    SocketCAN is only available under Linux.

.. automodule:: pykiso.lib.connectors.cc_socket_can.cc_socket_can
    :members:
    :private-members:
