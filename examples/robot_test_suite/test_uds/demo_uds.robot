*** Settings ***
Documentation   Robot framework Demo for uds auxiliary implementation
Library    pykiso.lib.robot_framework.uds_auxiliary.UdsAuxiliary    WITH NAME    UdsAux
Library    Collections

*** Test Cases ***

Go in default session
    [Documentation]    Send diagnostic session control request session
    ...                default using Send uds raw

    ${response} =  Send uds raw    \x10\x01    uds_aux

    Log  ${response}
