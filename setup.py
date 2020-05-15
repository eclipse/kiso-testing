#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="pykiso",
    version="0.1.0",
    license="Eclipse Public License - v 2.0",
    description="Embedded integration testing framework.",
    long_description=read("README.md"),
    author="Sebastian Fischer",
    author_email="sebastian.fischer@de.bosch.com",
    url="https://github.com/ionelmc/python-nameless",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
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
    keywords=["testing", "integration testing", "framework", "testing framework",],
    python_requires=">=3.6",
    install_requires=[
        "pyserial",
        "timeout-decorator",
        "click",
        "pyyaml",
        "pylink-square",
    ],
    tests_require=["pytest", "pytest-mock", "coverage"],
    extras_require={},
    setup_requires=[],
    entry_points={"console_scripts": ["pykiso = pykiso.cli:main",]},
)
