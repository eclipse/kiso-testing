##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import logging
import platform
import sys
from glob import glob
from os.path import basename, dirname, join, splitext
from pathlib import Path

from setuptools import find_packages, setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="pykiso",
    version="0.14.0",
    license="Eclipse Public License - v 2.0",
    description="Embedded integration testing framework.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Sebastian Fischer",
    author_email="sebastian.fischer@de.bosch.com",
    url="https://github.com/eclipse/kiso-testing",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    package_data={
        "": [
            "*.j2",
            "*.css",
        ]
    },
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
    keywords=[
        "testing",
        "integration testing",
        "framework",
        "testing framework",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pyserial",
        "timeout-decorator",
        "click",
        "pyyaml",
        "pylink-square",
        "python-can",
        "unittest-xml-reporting",
        "robotframework==3.2.2",
        "pyvisa",
        "pyvisa-py",
        "Jinja2",
    ],
    tests_require=["pytest", "pytest-mock", "coverage"],
    extras_require={},
    setup_requires=[],
    entry_points={
        "console_scripts": [
            "pykiso = pykiso.cli:main",
            "instrument-control = pykiso.lib.auxiliaries.instrument_control_auxiliary.instrument_control_cli:main",
        ]
    },
)
