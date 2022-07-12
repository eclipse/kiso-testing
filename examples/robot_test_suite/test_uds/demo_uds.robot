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

Use tester present sender
    [Documentation]    If no communication is exchanged with the client for more than 5
    ...                seconds the control unit automatically exits the current session and
    ...                returns to the "Default Session" back, and might go to sleep mode.
    ...
    ...                To avoid this issue if test steps take too long between uds commands,
    ...                the tester present sender can be use. It will send
    ...                at a define period a Tester Present, to signal to the device that
    ...                the client is still present.

    Start tester present sender 1 uds_aux
    ${response} =  Send uds raw    \x10\x03    uds_aux
    Stop tester present sender
