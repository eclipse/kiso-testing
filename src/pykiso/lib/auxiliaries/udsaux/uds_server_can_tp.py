##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
uds_auxiliary
*************

:module: uds_auxiliary

:synopsis: Auxiliary used to handle Unified Diagnostic Service protocol

.. currentmodule:: uds_auxiliary

"""
from collections import defaultdict
from time import sleep
from typing import Dict, List

from uds import ResettableTimer
from uds import fillArray
from uds.uds_communications.TransportProtocols.Can.CanTpTypes import (
    CanTpState,
    CanTpMessageType, 
    CanTpFsTypes, 
)
from uds.uds_communications.TransportProtocols.Can.CanTpTypes import (
    CANTP_MAX_PAYLOAD_LENGTH, 
    SINGLE_FRAME_DL_INDEX,
    FIRST_FRAME_DL_INDEX_HIGH, 
    FIRST_FRAME_DL_INDEX_LOW, 
    FC_BS_INDEX, 
    FC_STMIN_INDEX, 
    N_PCI_INDEX,
    FIRST_FRAME_DATA_START_INDEX, 
    SINGLE_FRAME_DATA_START_INDEX, 
    CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX,
    CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX, 
    FLOW_CONTROL_BS_INDEX, 
    FLOW_CONTROL_STMIN_INDEX
)
from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp

import xml.etree.ElementTree as ET
from uds import IsoServices


def parse(xmlFile) -> dict:

    sid_name = {
        0x10: "diagnosticSessionControl",
        0x11: "ecuReset",
        0x14: "clearDTC",
        0x19: "readDTC",
        0x22: "readDataByIdentifier",
        0x27: "securityAccess",
        0x2E: "writeDataByIdentifier",
        0x2F: "inputOutputControl",
        0x31: "routineControl",
        0x34: "requestDownload",
        0x35: "requestUpload",
        0x36: "transferData",
        0x37: "transferExit",
        0x3E: "testerPresent",
    }

    root = ET.parse(xmlFile)

    xmlElements = {}

    serviceConfigData = defaultdict(dict)

    for child in root.iter():
        try:
            xmlElements[child.attrib["ID"]] = child
        except KeyError:
            pass

    for value in xmlElements.values():
        if value.tag != "DIAG-SERVICE":
            continue

        did_config = {}

        sdg = value.find("SDGS").find("SDG")
        for sd in sdg:
            if sd.attrib.get("SI") == "DiagInstanceName":
                did_config["DID_Name"] = sd.text
                did_config["DID"] = []

        uds_request = []

        reqKey = value.find("REQUEST-REF").attrib["ID-REF"]
        reqElem = xmlElements[reqKey]

        params = reqElem.find("PARAMS")

        for param in params:

            semantic = param.attrib.get("SEMANTIC")

            if semantic is None:
                continue

            elif semantic == "SERVICE-ID":
                serviceId = int(param.find("CODED-VALUE").text)
                uds_request.append(serviceId)
                did_config["SID"] = serviceId
                did_config["SID_name"] = sid_name.get(serviceId)

                service_name = sid_name.get(serviceId)

                if service_name is None:
                    continue

                elif service_name not in serviceConfigData:
                    serviceConfigData[did_config["DID_Name"]].update({sid_name[serviceId]: []})

            elif semantic == "SUBFUNCTION":
                subId = int(param.find("CODED-VALUE").text)
                did_config["SubID"] = subId
                uds_request.append(subId)

            elif semantic == "ID":
                data = int(param.find("CODED-VALUE").text)
                dataLength = int(
                    int(param.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text) / 8
                )
                dataId = []
                for param in range(0, dataLength):
                    dataId.append((data >> (8 * (dataLength - param - 1))) & 0xFF)
                did_config["DID"].extend(dataId)
                uds_request.extend(dataId)

            elif semantic == "DATA":
                data_object_prop = param.find("DOP-REF")
                if data_object_prop is None:
                    continue
                paramKey = data_object_prop.attrib["ID-REF"]
                paramElem = xmlElements[paramKey]
                try:
                    paramLength = int(
                        int(
                            paramElem.find("DIAG-CODED-TYPE")
                            .find("BIT-LENGTH")
                            .text
                        )
                        / 8
                    )
                    uds_request.extend(paramLength * [0x00])
                except:
                    try:
                        try:
                            paramLength = int(paramElem.find("BYTE-SIZE").text)
                        except:
                            struct_params = paramElem.find("PARAMS")
                            paramLength = 0
                            for struct_param in struct_params:
                                structParamKey = struct_param.find(
                                    "DOP-REF"
                                ).attrib["ID-REF"]
                                structParamElem = xmlElements[structParamKey]
                                try:
                                    paramLength += int(
                                        int(
                                            structParamElem.find(
                                                "DIAG-CODED-TYPE"
                                            )
                                            .find("BIT-LENGTH")
                                            .text
                                        )
                                        / 8
                                    )
                                    delta = (
                                        0
                                        if int(
                                            int(
                                                structParamElem.find(
                                                    "DIAG-CODED-TYPE"
                                                )
                                                .find("BIT-LENGTH")
                                                .text
                                            )
                                            % 8
                                        )
                                        == 0
                                        else 1
                                    )
                                    paramLength += delta
                                except:
                                    try:
                                        paramLength += int(
                                            int(
                                                structParamElem.find(
                                                    "DIAG-CODED-TYPE"
                                                )
                                                .find("MIN-LENGTH")
                                                .text
                                            )
                                            / 8
                                        )
                                        delta = (
                                            0
                                            if int(
                                                int(
                                                    structParamElem.find(
                                                        "DIAG-CODED-TYPE"
                                                    )
                                                    .find("MIN-LENGTH")
                                                    .text
                                                )
                                                % 8
                                            )
                                            == 0
                                            else 1
                                        )
                                        paramLength += delta
                                    except:
                                        paramLength += 1
                        uds_request.extend(paramLength * [0x00])
                    except:
                        uds_request.append(0x00)

        did_config["UdsRequest"] = uds_request

        ############################################################
        ## RESPONSES
        ############################################################

        if value.attrib.get('TRANSMISSION-MODE') != 'SEND-ONLY':
            resp = _parse_response(xmlElements, value)
        
        conds = []
        #breakpoint()
        refs = value.find("PRE-CONDITION-STATE-REFS")
        if refs:
            for ref in refs:
                ref_id = ref.attrib["ID-REF"]
                ref_elem = xmlElements[ref_id]
                conds.append(ref_elem.find("SHORT-NAME").text)

        if conds == ["Programming"]:
            # critical uds services that only execute in programming
            did_config["Fbl"] = True
            did_config["Programming"] = True
            did_config["Locked"] = True
            did_config["BoschDev"] = True
            did_config["BoschProd"] = True
            serviceConfigData[did_config["DID_Name"]] = did_config
        elif (
            not conds 
            or not any(sess in conds for sess in ("BoschDev", "BoschProd"))
        ):
            did_config["Fbl"] = False
            did_config["Programming"] = True if not conds else False
            did_config["Locked"] = True
            did_config["BoschDev"] = True
            did_config["BoschProd"] = True
            serviceConfigData[did_config["DID_Name"]] = did_config
        else:
            did_config["Fbl"] = False
            did_config["Programming"] = False
            did_config["Locked"] = False
            did_config["BoschDev"] = "BoschDev" in conds
            did_config["BoschProd"] = "BoschProd" in conds
            serviceConfigData[did_config["DID_Name"]] = did_config

    return serviceConfigData


def _parse_request(xmlElements, value):
    uds_request = []

    reqKey = value.find("REQUEST-REF").attrib["ID-REF"]
    reqElem = xmlElements[reqKey]

    params = reqElem.find("PARAMS")

    for param in params:

        semantic = param.attrib.get("SEMANTIC")

        if semantic is None:
            continue

        elif semantic == "SERVICE-ID":
            serviceId = int(param.find("CODED-VALUE").text)
            uds_request.append(serviceId)
            did_config["SID"] = serviceId
            did_config["SID_name"] = sid_name.get(serviceId)

            service_name = sid_name.get(serviceId)

            if service_name is None:
                continue

            elif service_name not in serviceConfigData:
                serviceConfigData[did_config["DID_Name"]].update({sid_name[serviceId]: []})

        elif semantic == "SUBFUNCTION":
            subId = int(param.find("CODED-VALUE").text)
            did_config["SubID"] = subId
            uds_request.append(subId)

        elif semantic == "ID":
            data = int(param.find("CODED-VALUE").text)
            dataLength = int(
                int(param.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text) / 8
            )
            dataId = []
            for param in range(0, dataLength):
                dataId.append((data >> (8 * (dataLength - param - 1))) & 0xFF)
            did_config["DID"].extend(dataId)
            uds_request.extend(dataId)

        elif semantic == "DATA":
            data_object_prop = param.find("DOP-REF")
            if data_object_prop is None:
                continue
            paramKey = data_object_prop.attrib["ID-REF"]
            paramElem = xmlElements[paramKey]
            try:
                paramLength = int(
                    int(
                        paramElem.find("DIAG-CODED-TYPE")
                        .find("BIT-LENGTH")
                        .text
                    )
                    / 8
                )
                uds_request.extend(paramLength * [0x00])
            except:
                try:
                    try:
                        paramLength = int(paramElem.find("BYTE-SIZE").text)
                    except:
                        struct_params = paramElem.find("PARAMS")
                        paramLength = 0
                        for struct_param in struct_params:
                            structParamKey = struct_param.find(
                                "DOP-REF"
                            ).attrib["ID-REF"]
                            structParamElem = xmlElements[structParamKey]
                            try:
                                paramLength += int(
                                    int(
                                        structParamElem.find(
                                            "DIAG-CODED-TYPE"
                                        )
                                        .find("BIT-LENGTH")
                                        .text
                                    )
                                    / 8
                                )
                                delta = (
                                    0
                                    if int(
                                        int(
                                            structParamElem.find(
                                                "DIAG-CODED-TYPE"
                                            )
                                            .find("BIT-LENGTH")
                                            .text
                                        )
                                        % 8
                                    )
                                    == 0
                                    else 1
                                )
                                paramLength += delta
                            except:
                                try:
                                    paramLength += int(
                                        int(
                                            structParamElem.find(
                                                "DIAG-CODED-TYPE"
                                            )
                                            .find("MIN-LENGTH")
                                            .text
                                        )
                                        / 8
                                    )
                                    delta = (
                                        0
                                        if int(
                                            int(
                                                structParamElem.find(
                                                    "DIAG-CODED-TYPE"
                                                )
                                                .find("MIN-LENGTH")
                                                .text
                                            )
                                            % 8
                                        )
                                        == 0
                                        else 1
                                    )
                                    paramLength += delta
                                except:
                                    paramLength += 1
                    uds_request.extend(paramLength * [0x00])
                except:
                    uds_request.append(0x00)



def _parse_response(xmlElements, value):
    try:
        totalLength = 0
        sessionType = None

        positiveResponseElement = xmlElements[
            (value.find('POS-RESPONSE-REFS')).find('POS-RESPONSE-REF').attrib['ID-REF']
        ]

        paramsElement = positiveResponseElement.find('PARAMS')

        for param in paramsElement:

            semantic = param.attrib.get("SEMANTIC")
            if semantic is None:
                continue

            startByte = int(param.find('BYTE-POSITION').text)

            if semantic == "SERVICE-ID":
                # expected service ID
                responseId = int(param.find('CODED-VALUE').text)
                bitLength = int((param.find('DIAG-CODED-TYPE')).find('BIT-LENGTH').text)
                listLength = int(bitLength / 8)
                # service ID start
                responseIdStart = startByte
                # service ID end
                responseIdEnd = startByte + listLength
                totalLength += listLength

            elif semantic == "SUBFUNCTION" or semantic == "ID":
                # expected subfunction ID
                sessionType = param.find('CODED-VALUE')
                sessionType = int(sessionType.text)
                bitLength = int((param.find('DIAG-CODED-TYPE')).find('BIT-LENGTH').text)
                listLength = int(bitLength / 8)
                # subfunction ID start
                sessionTypeStart = startByte
                # subfunction ID start
                sessionTypeEnd = startByte + listLength
                totalLength += listLength

            elif semantic == "DATA":
                dataObjectElement = xmlElements[(param.find('DOP-REF')).attrib['ID-REF']]
                if dataObjectElement.tag == "DATA-OBJECT-PROP":
                    start = int(param.find('BYTE-POSITION').text)
                    fixed_data_length = dataObjectElement.find('DIAG-CODED-TYPE').find('BIT-LENGTH')
                    if fixed_data_length is None:
                        # has optional data 
                        bitLength = 0
                    else:
                        bitLength = int(fixed_data_length.text)
                    listLength = int(bitLength/8)
                    totalLength += listLength
                elif dataObjectElement.tag == "STRUCTURE":
                    start = int(param.find('BYTE-POSITION').text)
                    if dataObjectElement.find('BYTE-SIZE') is not None:
                        listLength = int(dataObjectElement.find('BYTE-SIZE').text)
                    else:
                        listLength = 64
                    totalLength += listLength   
        

        if sessionType is None:
            sessionType, sessionTypeStart, sessionTypeEnd = 0, 0, 0


        sub_function_len = sessionTypeEnd - sessionTypeStart 

        sessionType = (
            list(sessionType.to_bytes(sub_function_len, byteorder="big"))
            if sub_function_len > 1 else [sessionType]
        )

        resp_list = list()
        resp_list.extend([responseId])
        resp_list.extend(sessionType)
        resp_list.extend([0] * (totalLength - len(resp_list)))

        print(f"Expected service ID {responseId} from {responseIdStart} to {responseIdEnd}")
        print(f"Expected subfunction ID {sessionType} from {sessionTypeStart} to {sessionTypeEnd}")
        print("Expected response format:", [hex(el) for el in resp_list])

        return resp_list

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        breakpoint()




class ServerCanTp(CanTp):

    def __init__(self, configPath = None, callbacks: List[dict] = None, **kwargs):
        super().__init__(configPath=configPath, **kwargs)
        self.callbacks = callbacks

    ##
    # @breif decoding method
    # @param timeout_ms the timeout to wait before exiting
    # @param received_data the data that should be decoded in case of ITF Automation
    # @param use_external_snd_rcv_functions boolean to state if external sending and receiving functions shall be used
    # return a list
    def decode_isotp(self, timeout_s=1, received_data=None, use_external_snd_rcv_functions: bool = False):

        #return super().decode_isotp(
        #    received_data=payload, use_external_snd_rcv_functions=use_external_snd_rcv_functions
        #)

        timeoutTimer = ResettableTimer(timeout_s)

        payload = []
        payloadPtr = 0
        payloadLength = None

        sequenceNumberExpected = 1

        txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        endOfMessage_flag = False

        state = CanTpState.IDLE

        timeoutTimer.start()
        while endOfMessage_flag is False:

            rxPdu = self.getNextBufferedMessage()
            if use_external_snd_rcv_functions:
                rxPdu = received_data
            if rxPdu is not None:
                if rxPdu[N_PCI_INDEX] == 0x00:
                    rxPdu = rxPdu[1:]
                    N_PCI = 0
                else:
                    N_PCI = (rxPdu[N_PCI_INDEX] & 0xF0) >> 4
                if state == CanTpState.IDLE:
                    if N_PCI == CanTpMessageType.SINGLE_FRAME:
                        # received single frame, respond with single frame 
                        payloadLength = rxPdu[N_PCI_INDEX & 0x0F]
                        payload = rxPdu[SINGLE_FRAME_DATA_START_INDEX: SINGLE_FRAME_DATA_START_INDEX + payloadLength]
                        endOfMessage_flag = True
                    elif N_PCI == CanTpMessageType.FIRST_FRAME:
                        # received first frame, respond with flow control
                        payload = rxPdu[FIRST_FRAME_DATA_START_INDEX:]
                        payloadLength = ((rxPdu[FIRST_FRAME_DL_INDEX_HIGH] & 0x0F) << 8) + rxPdu[FIRST_FRAME_DL_INDEX_LOW]
                        payloadPtr = self.__maxPduLength - 1
                        state = CanTpState.SEND_FLOW_CONTROL
                elif state == CanTpState.RECEIVING_CONSECUTIVE_FRAME:
                    if N_PCI == CanTpMessageType.CONSECUTIVE_FRAME:
                        sequenceNumber = rxPdu[CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX] & 0x0F
                        if sequenceNumber != sequenceNumberExpected:
                            raise Exception("Consecutive frame sequence out of order")
                        else:
                            sequenceNumberExpected = (sequenceNumberExpected + 1) % 16
                        payload += rxPdu[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:]
                        payloadPtr += (self.__maxPduLength)
                        timeoutTimer.restart()
                    else:
                        raise Exception("Unexpected PDU received")
            else:
                sleep(0.01)

            if state == CanTpState.SEND_FLOW_CONTROL:
                txPdu[N_PCI_INDEX] = 0x30
                txPdu[FLOW_CONTROL_BS_INDEX] = 0
                txPdu[FLOW_CONTROL_STMIN_INDEX] = 0x1E
                self.transmit(txPdu)
                timeoutTimer.restart()
                state = CanTpState.RECEIVING_CONSECUTIVE_FRAME

            if payloadLength is not None:
                if payloadPtr >= payloadLength:
                    endOfMessage_flag = True

            if timeoutTimer.isExpired():
                raise Exception("Timeout in waiting for message")

        return list(payload[:payloadLength])


    ##
    # @brief encoding method
    # @param payload the payload to be sent
    # @param use_external_snd_rcv_functions boolean to state if external sending and receiving functions shall be used
    # @param [in] tpWaitTime time to wait inside loop
    def encode_isotp(self, payload, functionalReq: bool = False, use_external_snd_rcv_functions: bool = False, tpWaitTime = 0.01):

        #return super().encode_isotp(
        #    payload=received_data, 
        #    functionalReq=False, 
        #    use_external_snd_rcv_functions=use_external_snd_rcv_functions
        #)

        payloadLength = len(payload)
        payloadPtr = 0

        state = CanTpState.IDLE

        if payloadLength > CANTP_MAX_PAYLOAD_LENGTH:
            raise Exception("Payload too large for CAN Transport Protocol")

        if payloadLength < self.__maxPduLength:
            state = CanTpState.SEND_SINGLE_FRAME
        else:
            state = CanTpState.SEND_FIRST_FRAME

        txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        sequenceNumber = 1
        endOfMessage_flag = False

        blockList = []
        currBlock = []

        # this needs fixing to get the timing from the config
        # TODO: increase timer
        timeoutTimer = ResettableTimer(1)
        stMinTimer = ResettableTimer()

        data = None

        while endOfMessage_flag is False:
            rxPdu = self.getNextBufferedMessage()

            if rxPdu is not None:
                N_PCI = (rxPdu[0] & 0xF0) >> 4
                if N_PCI == CanTpMessageType.FLOW_CONTROL:
                    fs = rxPdu[0] & 0x0F
                    if fs == CanTpFsTypes.WAIT:
                        raise Exception("Wait not currently supported")
                    elif fs == CanTpFsTypes.OVERFLOW:
                        raise Exception("Overflow received from ECU")
                    elif fs == CanTpFsTypes.CONTINUE_TO_SEND:
                        if state == CanTpState.WAIT_FLOW_CONTROL:
                            if fs == CanTpFsTypes.CONTINUE_TO_SEND:
                                bs = rxPdu[FC_BS_INDEX]
                                if(bs == 0):
                                    bs = 585
                                blockList = self.create_blockList(payload[payloadPtr:],
                                                                  bs)
                                stMin = self.decode_stMin(rxPdu[FC_STMIN_INDEX])
                                currBlock = blockList.pop(0)
                                state = CanTpState.SEND_CONSECUTIVE_FRAME
                                stMinTimer.timeoutTime = stMin
                                stMinTimer.start()
                                timeoutTimer.stop()
                        else:
                            raise Exception("Unexpected Flow Control Continue to Send request")
                    else:
                        raise Exception("Unexpected fs response from ECU")
                else:
                    raise Exception("Unexpected response from device")

            if state == CanTpState.SEND_SINGLE_FRAME:
                if len(payload) <= self.__minPduLength:
                    txPdu[N_PCI_INDEX] += (CanTpMessageType.SINGLE_FRAME << 4)
                    txPdu[SINGLE_FRAME_DL_INDEX] += payloadLength
                    txPdu[SINGLE_FRAME_DATA_START_INDEX:] = fillArray(payload, self.__minPduLength)
                else:
                    txPdu[N_PCI_INDEX] = 0
                    txPdu[FIRST_FRAME_DL_INDEX_LOW] = payloadLength
                    txPdu[FIRST_FRAME_DATA_START_INDEX:] = payload
                data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                endOfMessage_flag = True
            elif state == CanTpState.SEND_FIRST_FRAME:
                payloadLength_highNibble = (payloadLength & 0xF00) >> 8
                payloadLength_lowNibble = (payloadLength & 0x0FF)
                txPdu[N_PCI_INDEX] += (CanTpMessageType.FIRST_FRAME << 4)
                txPdu[FIRST_FRAME_DL_INDEX_HIGH] += payloadLength_highNibble
                txPdu[FIRST_FRAME_DL_INDEX_LOW] += payloadLength_lowNibble
                txPdu[FIRST_FRAME_DATA_START_INDEX:] = payload[0:self.__maxPduLength - 1]
                payloadPtr += self.__maxPduLength - 1
                data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                timeoutTimer.start()
                state = CanTpState.WAIT_FLOW_CONTROL
            elif state == CanTpState.SEND_CONSECUTIVE_FRAME:
                if (stMinTimer.isExpired()):
                    txPdu[N_PCI_INDEX] += (CanTpMessageType.CONSECUTIVE_FRAME << 4)
                    txPdu[CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX] += sequenceNumber
                    txPdu[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:] = currBlock.pop(0)
                    payloadPtr += self.__maxPduLength
                    data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                    sequenceNumber = (sequenceNumber + 1) % 16
                    stMinTimer.restart()
                    if (len(currBlock) == 0):
                        if (len(blockList) == 0):
                            endOfMessage_flag = True
                        else:
                            timeoutTimer.start()
                            state = CanTpState.WAIT_FLOW_CONTROL
            else:
                sleep(tpWaitTime)
            txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            # timer / exit condition checks
            if timeoutTimer.isExpired():
                raise Exception("Timeout waiting for message")
        if use_external_snd_rcv_functions:
            return data


if __name__ == '__main__':

    from pprint import pprint
    parsed = parse("C:/Users/CLS1RT/Documents/01_Projets/EBike/Python/Automation/automated-bikeinthebox-integration/tests/walk_assist/BDU3xxx_V0.64.odx")
    pprint(parsed)

