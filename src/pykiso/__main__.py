##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Is used when pykiso is called as a module.

It redirects to pykiso.cli.main.

.. command-output:: python -m pykiso --help
    :ellipsis: 4



:module: __main__

"""

from .cli import main

if __name__ == "__main__":
    main()
