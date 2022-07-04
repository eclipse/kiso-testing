Multiprocessing
===============

Introduction
------------

In addition to the auxiliary's thread based implementation, the multiprocessing
approach is possible too. A dedicated multiprocessing auxiliary interface is
available and has the same capabilities/methods as the thread based
interface.

.. note:: all examples are under examples/templates/mp_proxy_aux.yaml

Basic Users
-----------

For the moment, only the proxy auxiliary and proxy channel have their
own multiprocessing version. The usage of those components only require
to manipulate the flag newly created flag "processing" at connector
configuration level as follow :

.. code:: python

    #__________________________ Auxiliaries section ________________________
    # The multiprocessing proxy auxiliary has exactly the same interface,
    # methods, or features as the thread based one. In addition, exactly
    # the same configuration keywords are available.
    auxiliaries:
      proxy_aux:
        connectors:
            com: can_channel
        config:
          aux_list : [aux1, aux2]
          activate_trace : True
          trace_dir: ./suite_mp_proxy
          trace_name: can_trace
          activate_log :
            - pykiso.lib.auxiliaries.mp_proxy_auxiliary
        type: pykiso.lib.auxiliaries.mp_proxy_auxiliary:MpProxyAuxiliary
      aux1:
        connectors:
            com: proxy_com1
        type: pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary
      aux2:
        connectors:
            com: proxy_com2
        type: pykiso.lib.auxiliaries.communication_auxiliary:CommunicationAuxiliary

    #__________________________ Connectors section _________________________
    connectors:
      proxy_com1:
        config:
          # when using mulitprocessing auxiliary flag processing has to True
          processing : True
        type: pykiso.lib.connectors.cc_mp_proxy:CCMpProxy
      proxy_com2:
        config:
          # when using mulitprocessing auxiliary flag processing has to True
          processing : True
        type: pykiso.lib.connectors.cc_mp_proxy:CCMpProxy
      can_channel:
        config:
          # when using mulitprocessing auxiliary flag processing has to True
          processing : True
          interface : 'pcan'
          channel: 'PCAN_USBBUS1'
          state: 'ACTIVE'
          remote_id : 0x300
        type: pykiso.lib.connectors.cc_pcan_can:CCPCanCan
    #__________________________ Test Suite section _________________________
    test_suite_list:
    - suite_dir: suite_proc_proxy
      test_filter_pattern: 'test_*.py'
      test_suite_id: 2

Advanced Users
--------------

As said before, the approach changes but the interface usage stays the same.
Advanced user will not be disorientated, all methods are there. They were
just adapted regarding multiprocessing pros and cons:

- lock_it
- unlock_it
- create_instance
- delete_instance
- run_command
- abort_command
- wait_and_get_report
- stop
- resume
- suspend

And inherit from the MpAuxiliaryInterface forces you to implement the
following methods (as usual):

 - _create_auxiliary_instance
 - _delete_auxiliary_instance
 - _run_command
 - _abort_command
 - _receive_message

So nothing really new !!

.. warning:: note that using multiprocessing auxiliary may lead to
    an adaptation of your connector implementation or your external libraries.

Limitations
-----------

Junit report logging
~~~~~~~~~~~~~~~~~~~~

Logging in junit report is not supported when using multiprocesssing version
of the proxy auxiliary. This means no logs from proxy auxiliary and his
associated connectors (except proxy channels) will be present in junit report.

logging on stdout
~~~~~~~~~~~~~~~~~

All logs coming from proxy's associated connectors (except proxy channels)
won't be displayed on the console.
