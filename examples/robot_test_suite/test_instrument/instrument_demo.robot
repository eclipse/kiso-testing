*** Settings ***
Documentation   Robot framework Demo for instrument control auxiliary implementation

Library    pykiso.lib.robot_framework.instrument_control_auxiliary.InstrumentControlAuxiliary    WITH NAME    InstAux

*** Test Cases ***

Use of global command read/write/query
    [Documentation]    Simply use the basic interface read, write
    ...                and query

    ${ident} =  Query    *IDN?    instr_aux

    Log  ${ident}

    ${state} =  Write    SOURce:VOLTage 36    instr_aux

    Should Be Equal    ${state}    NO_VALIDATION

    ${state} =  Write    SOURce:VOLTage?    instr_aux

    Should Be Equal    ${state}    NO_VALIDATION

    ${voltage} =  Read    instr_aux

    Log  ${voltage}

    ${validation} =  Create List    SOURce:VOLTage?    VALUE{40}

    ${state} =  Write    SOURce:VOLTage 40    instr_aux    ${validation}

    Should Be Equal    ${state}    SUCCESS


Query instrument information
    [Documentation]    Get instrument information identification, status
    ...                byte and current errors

    ${ident} =  Get identification    instr_aux

    ${status_byte} =  Get status byte    instr_aux

    ${errors} =  Get all errors    instr_aux

    Log  ${ident}

    Log  ${status_byte}

    Log  ${errors}

Reset instrument
    [Documentation]    Simply trigger instrument's reset

    ${state} =  Reset   instr_aux

    Should Be Equal    ${state}    NO_VALIDATION

Make a self test
    [Documentation]    Simply trigger instrument's self test

    ${verdict} =  Self test   instr_aux

    Should Be Equal    ${verdict}    0,"No error"

Get remote control state
    [Documentation]    Get current remote state, activate or not

    ${state} =  Get remote control state  instr_aux

    Should Be Equal    ${state}    REMOTE

Set remote control OFF/ON
    [Documentation]    Simply trigger remote control OFF an ON

    ${state_off} =  Set remote control ON  instr_aux

    ${state_on} =  Set remote control on  instr_aux

    Should Be Equal    ${state_off}    SUCCESS

    Should Be Equal    ${state_on}    SUCCESS

Get nominal values
    [Documentation]    Get all current nominal values voltage, current
    ...                and power

    ${nominal_voltage} =  Get nominal voltage    instr_aux

    ${nominal_current} =  Get nominal current    instr_aux

    ${nominal_power} =  Get nominal power    instr_aux

    Log  ${nominal_voltage}

    Log  ${nominal_current}

    Log  ${nominal_power}

Disable/Enable output
    [Documentation]    Simply deactivate and activate output

    ${state_off} =  Disable output    instr_aux

    ${state_on} =  Enable output    instr_aux

    Should Be Equal    ${state_off}    SUCCESS

    Should Be Equal    ${state_on}    SUCCESS

Set target voltage to 40.2V
    [Documentation]    Set target volatge to 40.2 V and check it

    ${state} =  Set target voltage    40.2    instr_aux

    Should Be Equal   ${state}    SUCCESS

    ${target_voltage} =  Get target voltage    instr_aux

    Log  ${target_voltage}

Set target current to 1.1A
    [Documentation]    Set target current to 1.1 A and check it

    ${state} =  Set target current    1.1    instr_aux

    Should Be Equal    ${state}    SUCCESS

    ${target_current} =  Get target current    instr_aux

    Log  ${target_current}

Set target power to 2W
    [Documentation]    Set target power to 2 W and check it

    ${state} =  Set target power    2    instr_aux

    Should Be Equal    ${state}    SUCCESS

    ${target_power} =  Get target power    instr_aux

    Log  ${target_power}

Measure values voltage, current and power
    [Documentation]    Measure current applied voltage, current and
    ...                power

    ${voltage} =  Measure voltage    instr_aux

    ${current} =  Measure current    instr_aux

    ${power} =  Measure power    instr_aux

    Log  ${voltage}

    Log  ${current}

    Log  ${power}

Get/Set voltage limit
    [Documentation]    Set voltage limit low and high [0 ; 45]V and
    ...                check it

    ${state_low} =  Set voltage limit low    0    instr_aux

    ${state_high} =  Set voltage limit high    45    instr_aux

    ${voltage_limit_low} =  Get voltage limit low    instr_aux

    ${voltage_limit_high} =  Get voltage limit high    instr_aux

    Should Be Equal    ${state_low}    SUCCESS

    Should Be Equal    ${state_high}    SUCCESS

    Should Be Equal    ${voltage_limit_low}    0.00 V

    Should Be Equal    ${voltage_limit_high}    45.00 V

Get/Set current limit
    [Documentation]    Set current limit low and high [0 ; 2]A and check
    ...                it

    ${state_low} =  Set current limit low    0    instr_aux

    ${state_high} =  Set current limit high    2    instr_aux

    ${current_limit_low} =  Get current limit low    instr_aux

    ${current_limit_high} =  Get current limit high    instr_aux

    Should Be Equal    ${state_low}    SUCCESS

    Should Be Equal    ${state_high}    SUCCESS

    Should Be Equal    ${current_limit_low}    0.000 A

    Should Be Equal    ${current_limit_high}    2.000 A

Get/Set power limit
    [Documentation]    Set power limit high to 2.0 W and check it

    ${state_high} =  Set power limit high    2    instr_aux

    ${power_limit_high} =  Get power limit high    instr_aux

    Should Be Equal    ${state_high}    SUCCESS

    Should Be Equal    ${power_limit_high}    2.0 W
