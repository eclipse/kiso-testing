.. _uds_auxiliary:

Using UDS protocol
==================

UdsAuxiliary class (:py:class:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary`) contained
in uds_auxiliary.py is the main interface between user and all the behind implemented logic. 
This class defines usable keywords(methods) for scripters in order to send a uds request to the device under test (raw or configurable)...

Send UDS Raw Request
--------------------
| Send UDS request as list of raw bytes.
| The method send_uds_raw(:py:meth:`pykiso.lib.auxiliaries.udsaux.UdsAuxiliary.send_uds_raw`) takes one mandatory parameter msg_to_send and one optional : timeout_in_s
| The parameter msg_to_send is simply the UDS request payload which is a list of bytes.
| The optional parameter timeout_in_s (by default fixed to 5 seconds) simply represent the maximum
  amount of time in second to wait for a response from the device under test. If this timeout is reached, the
  uds-auxiliary stop to acquire and log an error.

If the corresponding response is received from entity under test, send_uds_raw method returns it also as a list of bytes.
See example below:

.. code:: python

	import pykiso
	from pykiso.auxiliaries import uds_aux


	@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
	class ExampleUdsTest(pykiso.BasicTest):
	    def setUp(self):
	        """Hook method from unittest in order to execute code before test case run."""
	        pass

	    def test_run(self):
	        logging.info(
	            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
	        )

	        """
	        Simply go in extended session.

	        The equivalent command using an ODX file would be :

	        extendedSession_req = {
	            "service": IsoServices.DiagnosticSessionControl,
	            "data": {"parameter": "Extended Diagnostic Session"},
	        }
	        diag_session_response = uds_aux.send_uds_config(extendedSession_req)
	        """
	        diag_session_response = uds_aux.send_uds_raw([0x10, 0x01])
	        self.assertEqual(diag_session_response[:2], [0x50, 0x01])

	    def tearDown(self):
	        """Hook method from unittest in order to execute code after test case run."""
	        pass

Send UDS Config Request
-----------------------
| Send UDS request as a configurable data dictionary. This method can be more practical for UDS requests with long payloads and a multitude of parameters.
| The method send_uds_config(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.send_uds_config`) takes one mandatory parameter msg_to_send and an optional one timeout_in_s.
| The parameter msg_to_send is the UDS request defined as a configurable dictionary that always respects the below defined template:

.. code:: python

    req = {
        'service'   : %SERVICE_ID%,
        'data'      : %DATA%
        }

SERVICE_ID -> SID (Service Identifier) of the UDS request either defined as a byte or the corresponding enum label:

.. code:: python

    class IsoServices(IntEnum):
        DiagnosticSessionControl = 0x10
        EcuReset = 0x11
        SecurityAccess = 0x27
        CommunicationControl = 0x28
        TesterPresent = 0x3E
        AccessTimingParameter = 0x83
        SecuredDataTransmission = 0x84
        ControlDTCSetting = 0x85
        ResponseOnEvent = 0x86
        LinkControl = 0x87
        ReadDataByIdentifier = 0x22
        ReadMemoryByAddress = 0x23
        ReadScalingDataByIdentifier = 0x24
        ReadDataByPeriodicIdentifier = 0x2A
        DynamicallyDefineDataIdentifier = 0x2C
        WriteDataByIdentifier = 0x2E
        WriteMemoryByAddress = 0x3D
        ClearDiagnosticInformation = 0x14
        ReadDTCInformation = 0x19
        InputOutputControlByIdentifier = 0x2F
        RoutineControl = 0x31
        RequestDownload = 0x34
        RequestUpload = 0x35
        TransferData = 0x36
        RequestTransferExit = 0x37

| DATA -> dictionary that contains the following keys:
|     - 'parameter': DID (Data Identifier) of the UDS request. (In most UDS services with DID)
|     - %param_n%: one or many keys that represent the parameters related to the service, those depend on ODX definition that is tested.

See some examples of UDS requests below:

.. code:: python

    import pykiso
    from pykiso.auxiliaries import uds_aux
    from uds import IsoServices

    @pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[uds_aux])
    class ExampleUdsTest(pykiso.BasicTest):
        def setUp(self):
            """Hook method from unittest in order to execute code before test case run.
            """
            pass

        def test_run(self):
	        extendedSession_req = {
	            "service": IsoServices.DiagnosticSessionControl,
	            "data": {"parameter": "Extended Diagnostic Session"},
	        }
	        diag_session_response = uds_aux.send_uds_config(extendedSession_req)

        def tearDown(self):
            """Hook method from unittest in order to execute code after test case run.
            """
            pass


The optional parameter timeout_in_s (by default fixed to 6 seconds) simply represents the maximum
amount of time in second to wait for a response from the device under test. If this timeout is reached, the
uds-auxiliary stops to acquire and log an error.

| If the corresponding response is received from entity under test, send_uds_config method returns it also as a preconfigured dictionary.
| In case of a UDS positive response and no data to be returned, None is returned by the send_uds_config method.

UDS Reset functions
--------------------
|Reset might be integrated in different tests.
|The methods :  - soft_rest(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.soft_reset`)
|               - hard_reset(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.hard_reset`)
|               - key_off_on(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.key_off_on_reset`)
|do not take any argument, and regarding the config (with our without odx file) will send either raw message, or
|uds config (except for the key_off_on methods, but can remain acceptable for odx uds config)

.. code:: python
    #Soft reset
    uds_aux.soft_reset()

UDS check functions
--------------------
|Check functions might be integrated in different tests.
|The methods :  - check_raw_response_negative(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.check_raw_response_negative`)
|               - check_raw_response_positive(:py:meth:`pykiso.lib.auxiliaries.udsaux.uds_auxiliary.UdsAuxiliary.check_raw_response_positive`)
|The methods take one mandatory argument resp.
|The parameter rest is the response as a userlist object

.. code:: python
    #Check raw response is positive
    uds_aux.check_raw_response_positive(resp)

    #Check raw response is negative
    uds_aux.check_raw_response_negative(resp)
