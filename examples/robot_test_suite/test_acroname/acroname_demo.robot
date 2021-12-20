*** Settings ***
Documentation   Robot framework Demo for acroname auxiliary implementation

Library    pykiso.lib.robot_framework.acroname_auxiliary.AcronameAuxiliary    WITH NAME    AcroAux

*** Variables ***
${NO_ERROR} =    ${0}

*** Test Cases ***

Disable / Enable USB Ports
    [Documentation]    Disable and Enable USB Ports

    Log    Disable all Ports

    FOR    ${index}    IN RANGE    0    4
        Log    Disable USB port ${index}
        ${state}  Set port disable    acroname_aux    ${index}
        Should Be Equal   ${state}    ${NO_ERROR}
    END

    Sleep    1s

    FOR    ${index}    IN RANGE    0    4
        Log    Enable USB port ${index}
        ${state}  Set port disable    acroname_aux    ${index}
        Should Be Equal   ${state}    ${NO_ERROR}
    END

    Sleep    1s

Get Port Current
    [Documentation]    Read usb port current

    Log    Read port current

    FOR    ${index}    IN RANGE    0    4
        ${current}  Get port current    acroname_aux    ${index}    mA
        Log    Current on port ${index} is ${current} mA
    END

    Sleep    1s

Get Port Voltage
    [Documentation]    Read usb port voltage

    Log    Read port voltage

    FOR    ${index}    IN RANGE    0    4
        ${voltage}  Get port voltage    acroname_aux    ${index}    mV
        Log    Voltage on port ${index} is ${voltage} mV
    END

    Sleep    1s

Set Port Current Limit
    [Documentation]    Set usb port current

    Log    Read port current

    FOR    ${index}    IN RANGE    0    4
        Log    Set port current on port ${index} to 500 mA
        ${state}  Set port current limit    acroname_aux    ${index}    ${500}    mA
        Should Be Equal   ${state}    ${NO_ERROR}
    END

    Sleep    1s

Get Port Current Limit
    [Documentation]    Get usb port current limit

    Log    Read port current

    FOR    ${index}    IN RANGE    0    4
        ${current}  Get port current limit    acroname_aux    ${index}    mA
        Log    Port limit on port ${index} is ${current} mA
    END

    Sleep    1s

Set Port Current Limit to max
    [Documentation]    Set usb port current limit

    Log    Read port current

    FOR    ${index}    IN RANGE    0    4
        Log    Set port current on port ${index} to 1500 mA
        ${state}  Set port current limit    acroname_aux    ${index}    ${1500}    mA
        Should Be Equal   ${state}    ${NO_ERROR}
    END

    Sleep    1s
