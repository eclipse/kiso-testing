##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Library of instruments communicating via VISA
*********************************************

:module: lib_instruments

:synopsis: Dictionaries containing the appropriate SCPI commands for
    some instruments.

.. currentmodule:: lib_instruments

"""

REGISTERED_INSTRUMENTS = [
    "Elektro-Automatik",
    "Rohde&Schwarz",
]

SCPI_COMMANDS_DICT = {
    # General
    "IDENTIFICATION": {
        "query": {"DEFAULT": "*IDN?"},
        "write": {"DEFAULT": "NOT_AVAILABLE"},
    },
    "STATUS_BYTE": {
        "query": {"DEFAULT": "*STB?"},
        "write": {"DEFAULT": "NOT_AVAILABLE"},
    },
    "ALL_ERRORS": {
        "query": {"DEFAULT": "SYST:ERR:ALL?", "Rohde&Schwarz": "NOT_AVAILABLE"},
        "write": {"DEFAULT": "NOT_AVAILABLE"},
    },
    "SELF_TEST": {
        "query": {"DEFAULT": "*TST?"},
        "write": {"DEFAULT": "*TST"},
    },
    # Remote control
    "REMOTE_CONTROL": {
        "query": {"DEFAULT": "SYST:LOCK:OWN?", "Rohde&Schwarz": "NOT_AVAILABLE"},
        "write": {"DEFAULT": "SYST:LOCK", "Rohde&Schwarz": "NOT_AVAILABLE"},
    },
    # Output selection and enable
    "OUTPUT_CHANNEL": {
        "query": {
            "DEFAULT": "INST:NSEL?",
            "Elektro-Automatik": "NOT_AVAILABLE",
        },
        "write": {
            "DEFAULT": "INST:NSEL",
            "Elektro-Automatik": "NOT_AVAILABLE",
        },
    },
    "OUTPUT_ENABLE": {
        "query": {"DEFAULT": "OUTP?"},
        "write": {"DEFAULT": "OUTP"},
    },
    # Nominal values
    "NOMINAL_VOLTAGE": {
        "query": {
            "DEFAULT": "SYSTem:NOMinal:VOLTage?",
            "Rohde&Schwarz": "NOT_AVAILABLE",
        },
        "write": {"DEFAULT": "NOT_AVAILABLE?", "Rohde&Schwarz": "NOT_AVAILABLE"},
    },
    "NOMINAL_CURRENT": {
        "query": {
            "DEFAULT": "SYSTem:NOMinal:CURRent?",
            "Rohde&Schwarz": "NOT_AVAILABLE",
        },
        "write": {"DEFAULT": "NOT_AVAILABLE?", "Rohde&Schwarz": "NOT_AVAILABLE"},
    },
    "NOMINAL_POWER": {
        "query": {"DEFAULT": "SYSTem:NOMinal:POWer?", "Rohde&Schwarz": "NOT_AVAILABLE"},
        "write": {"DEFAULT": "NOT_AVAILABLE", "Rohde&Schwarz": "NOT_AVAILABLE"},
    },
    # Output measurement
    "MEASURE_VOLTAGE": {
        "query": {
            "DEFAULT": "MEASure:VOLTage?",
        },
        "write": {
            "DEFAULT": "NOT_AVAILABLE",
        },
    },
    "MEASURE_CURRENT": {
        "query": {
            "DEFAULT": "MEASure:CURRent?",
        },
        "write": {
            "DEFAULT": "NOT_AVAILABLE",
        },
    },
    "MEASURE_POWER": {
        "query": {
            "DEFAULT": "MEASure:POWer?",
        },
        "write": {"DEFAULT": "NOT_AVAILABLE"},
    },
    # Output desired values and limits
    "VOLTAGE": {
        "query": {"DEFAULT": "SOURce:VOLTage?"},
        "write": {"DEFAULT": "SOURce:VOLTage"},
    },
    "CURRENT": {
        "query": {"DEFAULT": "SOURce:CURRent?"},
        "write": {"DEFAULT": "SOURce:CURRent"},
    },
    "POWER": {
        "query": {"DEFAULT": "SOURce:POWer?", "Rohde&Schwarz": "NOT_AVAILABLE"},
        "write": {"DEFAULT": "SOURce:POWer", "Rohde&Schwarz": "NOT_AVAILABLE"},
    },
    "VOLTAGE_LIMIT_LOW": {
        "query": {
            "DEFAULT": "SOURce:VOLTage:LIMit:LOW?",
            "Rohde&Schwarz": "VOLT:ALIM:LOW?",
        },
        "write": {
            "DEFAULT": "SOURce:VOLTage:LIMit:LOW",
            "Rohde&Schwarz": "VOLT:ALIM:LOW",
        },
    },
    "VOLTAGE_LIMIT_HIGH": {
        "query": {
            "DEFAULT": "SOURce:VOLTage:LIMit:HIGH?",
            "Rohde&Schwarz": "VOLTage:ALIM?",
        },
        "write": {
            "DEFAULT": "SOURce:VOLTage:LIMit:HIGH",
            "Rohde&Schwarz": "VOLTage:ALIM",
        },
    },
    "CURRENT_LIMIT_LOW": {
        "query": {
            "DEFAULT": "SOURce:CURRent:LIMit:LOW?",
            "Rohde&Schwarz": "CURRent:ALIM:LOW?",
        },
        "write": {
            "DEFAULT": "SOURce:CURRent:LIMit:LOW",
            "Rohde&Schwarz": "CURRent:ALIM:LOW",
        },
    },
    "CURRENT_LIMIT_HIGH": {
        "query": {
            "DEFAULT": "SOURce:CURRent:LIMit:HIGH?",
            "Rohde&Schwarz": "CURRent:ALIM?",
        },
        "write": {
            "DEFAULT": "SOURce:CURRent:LIMit:HIGH",
            "Rohde&Schwarz": "CURRent:ALIM",
        },
    },
    "POWER_LIMIT_HIGH": {
        "query": {
            "DEFAULT": "SOURce:POWer:LIMit:HIGH?",
            "Rohde&Schwarz": "NOT_AVAILABLE",
        },
        "write": {
            "DEFAULT": "SOURce:POWer:LIMit:HIGH",
            "Rohde&Schwarz": "NOT_AVAILABLE",
        },
    },
}
