.. _uds_server_auxiliary:

UDS protocol handling as a server
================================

The :py:class:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary`_
implements the Unified Diagnostic Services protocol on server side and therefore acts
as an Electronic Control Unit communicating with a tester.

It allows the registration of callbacks through the helper class
:py:class:`~pykiso.lib.auxiliaries.udsaux.common.uds_callback.UdsCallback`_
or simply by specifying the arguments of
:py:meth:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.register_callback`_,
that are then triggered when the registered UDS request is received, allowing to respond with
user-defined UDS messages.

Configuration
~~~~~~~~~~~~~

To configure the UDS server auxiliary 1 parameter is mandatory :

- `config_ini_path`_: path to the UDS parameters configuration file (see format below).

It also accepts three optional parameters:

- `request_id`_: CAN identifier of the UDS responses send by the auxiliary
    (overrides the one defined in the config.ini file)
- `response_id`_: CAN identifier of the UDS requests received by the auxiliary
    (overrides the one defined in the config.ini file)
- `odx_file_path`_: path to the ECU diagnostic definition file in ODX format

.. note:: the configuration through an ODX file is not supported yet.

Find below a complete configuration example :

.. code:: yaml

    auxiliaries:
        uds_aux:
            connectors:
                com: can_channel
            config:
                odx_file_path: ./path/to/my/file.odx
                # For Vector Box, serial number and interface needs to be updated in config.ini file
                # request and response id need to be configured in config.ini if not specified
                # by the request_id and response_id parameters
                config_ini_path: ./test_uds/config.ini
                # override the CAN IDs specified in the config.ini file
                request_id: 0x123
                response_id: 0x321
            type: pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary:UdsServerAuxiliary
    connectors:
        can_channel:
            config:
            interface: 'pcan'
            channel: 'PCAN_USBBUS1'
            state: 'ACTIVE'
            type: pykiso.lib.connectors.cc_pcan_can:CCPCanCan
    test_suite_list:
    -   suite_dir: ./test_uds
        test_filter_pattern: 'test_uds_server.py'
        test_suite_id: 1

And for the config.ini file:

.. code:: ini

    [can]
    interface=peak
    canfd=True
    baudrate=500000
    data_baudrate=2000000
    defaultReqId=0xAC
    defaultResId=0xDC

    [uds]
    transportProtocol=CAN
    P2_CAN_Client=5
    P2_CAN_Server=1

    [canTp]
    reqId=0xAC
    resId=0xDC
    addressingType=NORMAL
    N_SA=0xFF
    N_TA=0xFF
    N_AE=0xFF
    Mtype=DIAGNOSTICS
    discardNegResp=False

    [virtual]
    interfaceName=virtualInterface

    [peak]
    device=PCAN_USBBUS1
    f_clock_mhz=80
    nom_brp=2
    nom_tseg1=63
    nom_tseg2=16
    nom_sjw=16
    data_brp=4
    data_tseg1=7
    data_tseg2=2
    data_sjw=2

    [vector]
    channel=1
    appName=MyApp

    [socketcan]
    channel=can0


Configuring UDS callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~

In order to configure callbacks to be triggered on a received request, the
:py:meth:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.register_callback`_
needs to be called.

The available parameters for defining a callback are the following:

- `request`_ (mandatory): the incoming UDS request on which the corresponding callback should be executed.
    The request can be passed as an integer (e.g. `0x1003`_ or as a list of integers `[0x10, 0x03]`_).
- `response`_ (optional): the UDS response to send if the registered request is received.
    Passed format is the same as for the request parameter.
- `response_data`_ (optional): the UDS data to send with the response. If the response is specified
    the data is simply appended to the response. This parameter can be passed as an integer or as
    bytes (e.g. `b"DATA"`_).
- `data_length`_ (optional): the expected length of the data to send within the response, as an integer.
    This parameter in only taken into account if the `response_data`_ parameter is specified and
    applied zero-padding to the response if the data to send is expected to have a fixed length.
- `callback`_ (optional): a user-defined callback function to execute. If this parameter is provided,
    all others optional parameters are discarded. The callback function must admit 2 positional
    arguments: the request on which the callback function is executed and the
    :py:class:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary`_ instance
    that registered the callback.

.. note::
    If the `response`_ parameter is not specified, the response will be built based on the
    `request`_ parameter. For example, a request `0x10020304`_ will produce the corresponding
    response `0x50020304`_.

In order to define and register callbacks for a test, two ways are made possible:

- With the helper class :py:class:`~pykiso.lib.auxiliaries.udsaux.common.uds_callback.UdsCallback`_
    in order to define the callbacks, and register them later.
- With the method :py:meth:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.register_callback`_
    in order to define and register a callback at the same time.

Split definition and registration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`~pykiso.lib.auxiliaries.udsaux.common.uds_callback.UdsCallback`_ can be imported
from directly from :py:mod:`pykiso.lib.udsaux` and allow an easy definition of callbacks that
are common to multiple test cases.

It takes the same parameters as :py:meth:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.register_callback`_
but allows to define the callbacks in order to register them afterwards.

Pykiso also defined a callback subclass for the UDS data download functional unit that can be
directly imported and re-used, or taken as a reference in order to implement other functional
UDS units: :py:class:`~pykiso.lib.auxiliaries.udsaux.common.uds_callback.UdsDownloadCallback`_.

Find below an example:

.. code:: python

    # helper objects to build callbacks can be imported from the pykiso lib
    from pykiso.lib.auxiliaries.udsaux import UdsCallback, UdsDownloadCallback

    # callbacks to register can then be built and stored in a list in order to be registered in tests
    UDS_CALLBACKS = [
        # Here the response could be left out
        # It would be automatically built based on the request
        UdsCallback(request=0x3E00, response=0x7E00),

        # The download functional unit is available as a pre-defined callback
        # It only requires the stmin parameter (minimum time between 2 consecutive frames, here 10ms)
        # Others (RequestUpload, RequestFileTransfer) can be implemented based on it.
        UdsDownloadCallback(stmin=10),

        # define a callback for incoming read data by identifier request with identifier [0x01, 0x02]
        # the response will be built by:
        # - creating the positive response corresponding to the request: 0x620102
        # - appending the passed response data b'DATA': 0x620102_44415451
        # - zero-padding the response data until the expected length is reached: 0x620102_44415451_0000
        UdsCallback(request=0x220102, response_data=b'DATA', data_len=6)
    ]


Admitting that this code is added to a `uds_callback_definition.py`_ file at the same level as
the test case, it can then be registered inside a test as follows:

.. code:: python

    import pykiso
    from pykiso.auxiliaries import uds_aux

    from uds_callback_definition import UDS_CALLBACKS

    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
    class ExampleUdsServerTest(pykiso.BasicTest):

        def setUp(self):
            """Register callbacks from an external file for the test."""

            for callback in UDS_CALLBACKS:
                uds_aux.register_callback(callback)

        def test_run(self):
            """Actual test."""
            ...

        def tearDown(self):
            """Unregister all callbacks from the external file."""
            for callback in UDS_CALLBACKS:
                uds_aux.register_callback(callback)

In-test definition and registration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The method :py:meth:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.register_callback`_
can be used inside a test case to define and register a callback with one line.

It admits the same parameters as :py:class:`~pykiso.lib.auxiliaries.udsaux.common.uds_callback.UdsCallback`_
and builds instances of it in the background.

Find below an example showing its usage, along with a custom callback function definition:

.. code:: python

    import typing

    import pykiso
    from pykiso.auxiliaries import uds_aux

    # only used for type-hinting the custom callback
    from pykiso.lib.auxiliaries.udsaux import UdsServerAuxiliary

    def custom_callback(ecu_reset_request: typing.List[int], aux: UdsServerAuxiliary) -> None:
        """Custom callback example for an ECU reset request.

        This simulates a pending response from the server before sending the
        corresponding positive response.

        :param ecu_reset_request: received ECU reset request from the client.
        :param aux: current UdsServerAuxiliary instance used in test.
        """
        for _ in range(4):
            aux.send_response([0x7F, 0x78])
            time.sleep(0.1)
        aux.send_response([0x51, 0x01])


    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
    class ExampleUdsServerTest(pykiso.BasicTest):

        def setUp(self):
            """Register various callbacks for the test."""
            # handle extended diagnostics session request
            # respond to an incoming request [0x10, 0x03] with [0x50, 0x03, 0x12, 0x34]
            uds_aux.register_callback(request=0x1003, response=0x50031234)

            # handle incoming read data by identifier request with identifier [0x01, 0x02]
            # the response will be built by:
            # - creating the positive response corresponding to the request: 0x620102
            # - appending the passed response data b'DATA': 0x620102_44415451
            # - zero-padding the response data until the expected length is reached: 0x620102_44415451_0000
            uds_aux.register_callback(request=0x220102, response_data=b'DATA', data_length=6)

            # register the custom callback defined above
            uds_aux.register_callback(request=0x1101, callback=custom_callback)

        def test_run(self):
            """Actual test."""
            ...

        def tearDown(self):
            """Unregister all callbacks registered by the auxiliary."""

            for callback in uds_aux.callbacks:
                uds_aux.unregister_callback(callback)

Accessing UDS callbacks
~~~~~~~~~~~~~~~~~~~~~~~

Once registered, callbacks can be accessed inside a test via the
:py:attr:`~pykiso.lib.auxiliaries.udsaux.uds_server_auxiliary.UdsServerAuxiliary.callbacks`_ attribute.
This attribute is a dictionary linking the registered request as an **uppercase** hexadecimal string
(e.g. `"0x2E0102"`_) to the corresponding registered callback.

Accessing a callback can be useful for verifying if a callback was called at some point. Based on
the test snippets above, the following complete test example aims to show this feature and provided
an overview of all previously described features:

.. code:: python

    import typing

    import pykiso
    from pykiso.auxiliaries import uds_aux

    # only used for type-hinting the custom callback
    from pykiso.lib.auxiliaries.udsaux import UdsServerAuxiliary

    from uds_callback_definition import UDS_CALLBACKS

    def custom_callback(ecu_reset_request: typing.List[int], aux: UdsServerAuxiliary) -> None:
        """Custom callback example for an ECU reset request.

        This simulates a pending response from the server before sending the
        corresponding positive response.

        :param ecu_reset_request: received ECU reset request from the client.
        :param aux: current UdsServerAuxiliary instance used in test.
        """
        for _ in range(4):
            aux.send_response([0x7F, 0x78])
            time.sleep(0.1)
        aux.send_response([0x51, 0x01])


    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
    class ExampleUdsServerTest(pykiso.BasicTest):

        def setUp(self):
            """Register various callbacks for the test."""
            # register external pre-defined callbacks
            for callback in UDS_CALLBACKS:
                uds_aux.register_callback(callback)

            # handle extended diagnostics session request [0x10, 0x03]
            uds_aux.register_callback(request=0x1003, response=0x50031234)

            # handle incoming read data by identifier request with identifier [0x01, 0x02]
            uds_aux.register_callback(request=0x220102, response_data=b'DATA', data_length=6)

        def test_run(self):
            """Actual test. Simply wait a bit and expect the registered request to be received
            (and the corresponding response to be sent to the client).
            """
            logging.info(
                f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
            )
            time.sleep(10)
            # access the previously registered callback
            extended_diag_session_callback = uds_aux.callbacks["0x1003"]
            self.assertGreater(
                extended_diag_session_callback.call_count,
                0,
                "Expected UDS request was not sent by the client after 10s",
            )

        def tearDown(self):
            """Unregister all callbacks registered by the auxiliary."""

            for callback in uds_aux.callbacks:
                uds_aux.unregister_callback(callback)
