*** Settings ***
Documentation   Test demo with RobotFramework and ITF TestApp

Library    pykiso.lib.robot_framework.dut_auxiliary.DUTAuxiliary    WITH NAME    DutAux

Suite Setup       Setup Aux

*** Keywords ***
Setup Aux
    @{auxiliaries} =    Create List  dut_aux1  dut_aux2
    Set Suite Variable  @{suite_auxiliaries}  @{auxiliaries}

*** Variables ***

*** Test Cases ***

Test TEST_SUITE_SETUP
    [Documentation]   Setup test suite on DUT
    Test App    TEST_SUITE_SETUP  1  1  ${suite_auxiliaries}

Test TEST_CASE_SETUP
    [Documentation]   Setup test case on DUT
    Test App    TEST_CASE_SETUP  1  1  ${suite_auxiliaries}

Test TEST_CASE_RUN
    [Documentation]   Run test case on DUT
    Test App    TEST_CASE_RUN  1  1  ${suite_auxiliaries}

Test TEST_CASE_TEARDOWN
    [Documentation]   Teardown test case on DUT
    Test App    TEST_CASE_TEARDOWN  1  1  ${suite_auxiliaries}

Test TEST_SUITE_TEARDOWN
    [Documentation]   Teardown test suite on DUT
    Test App    TEST_SUITE_TEARDOWN  1  1  ${suite_auxiliaries}
