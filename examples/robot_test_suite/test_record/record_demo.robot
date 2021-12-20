*** Settings ***
Documentation   Robot framework Demo for record auxiliary

# Library import will start recording
Library    pykiso.lib.robot_framework.record_auxiliary.RecordAuxiliary

*** Keywords ***

*** Test Cases ***

Test Something
    [Documentation]    Record channel in the background

    Sleep    5s
