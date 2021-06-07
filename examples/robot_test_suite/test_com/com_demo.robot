*** Settings ***
Documentation   Robot framework Demo for communication auxiliary implementation

Library    pykiso.lib.robot_framework.communication_auxiliary.CommunicationAuxiliary    WITH NAME    ComAux

*** Keywords ***

send raw message
    [Arguments]  ${raw_msg}  ${aux}
    ${is_executed}=    ComAux.Send message    ${raw_msg}    ${aux}
    [return]  ${is_executed}

get raw message
    [Arguments]  ${aux}  ${blocking}  ${timeout}
    ${msg}  ${source}=    ComAux.Receive message    ${aux}    ${blocking}    ${timeout}
    [return]  ${msg}  ${source}

*** Test Cases ***

Test send raw bytes using keywords
    [Documentation]    Simply send raw bytes over configured channel
    ...                using defined keywords

    ${state}  send raw message    \x01\x02\x03    aux1

    Log    ${state}

    Should Be Equal   ${state}    ${TRUE}

    ${msg}  ${source}  get raw message    aux1    ${TRUE}    0.5

    Log    ${msg}

Test send raw bytes
    [Documentation]    Simply send raw bytes over configured channel
    ...                using communication auxiliary methods directly

    ${state} =  Send message    \x04\x05\x06    aux2

    Log    ${state}

    Should Be Equal   ${state}    ${TRUE}

    ${msg}  ${source} =  Receive message    aux2    ${FALSE}    0.5

    Log    ${msg}
