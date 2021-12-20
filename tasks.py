##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Tasks for maintaining the project.

Execute 'invoke --list' for guidance on using Invoke
"""
import pathlib
import platform
import re
import shutil
import webbrowser
from pathlib import Path

from invoke import task

ROOT_DIR = Path(__file__).parent
TEST_DIR = ROOT_DIR / "tests"
COVERAGE_DIR = TEST_DIR / "coverage_report.html"
SOURCE_DIR = ROOT_DIR / "src"
DOCS_DIR = ROOT_DIR / "docs"
DOCS_BUILD_DIR = DOCS_DIR / "_build"
DOCS_INDEX = DOCS_BUILD_DIR / "index.html"
PYTHON_DIRS = [str(d) for d in [SOURCE_DIR, TEST_DIR]]

COPYRIGHT = """\
##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""


def _delete_file(file):
    try:
        file.unlink(missing_ok=True)
    except TypeError:
        # missing_ok argument added in 3.8
        try:
            file.unlink()
        except FileNotFoundError:
            pass


@task
def test(c):
    """
    Run tests
    """
    pty = platform.system() == "Linux"
    c.run("pytest")


@task
def docs(c):
    """
    Generate documentation
    """
    c.run("sphinx-build -b html {} {}".format(DOCS_DIR, DOCS_BUILD_DIR))
    webbrowser.open(DOCS_INDEX.as_uri())


@task
def clean_docs(c):
    """
    Clean up files from documentation builds
    """
    c.run("rm -fr {}".format(DOCS_BUILD_DIR))


@task
def clean_build(c):
    """
    Clean up files from package building
    """
    c.run("rm -fr build/")
    c.run("rm -fr dist/")
    c.run("rm -fr .eggs/")
    c.run("find . -name '*.egg-info' -exec rm -fr {} +")
    c.run("find . -name '*.egg' -exec rm -f {} +")


@task
def clean_python(c):
    """
    Clean up python file artifacts
    """
    c.run("find . -name '*.pyc' -exec rm -f {} +")
    c.run("find . -name '*.pyo' -exec rm -f {} +")
    c.run("find . -name '*~' -exec rm -f {} +")
    c.run("find . -name '__pycache__' -exec rm -fr {} +")


@task
def clean_tests(c):
    """
    Clean up files from testing
    """
    # shutil.rmtree(TOX_DIR, ignore_errors=True)
    shutil.rmtree(COVERAGE_DIR, ignore_errors=True)


@task(pre=[clean_build, clean_python, clean_tests, clean_docs])
def clean(c):
    """
    Runs all clean sub-tasks
    """
    pass


@task(clean)
def dist(c):
    """
    Build source and wheel packages
    """
    c.run("python setup.py sdist")
    c.run("python setup.py bdist_wheel")


@task(pre=[clean, dist])
def release(c):
    """
    Make a release of the python package to pypi
    """
    c.run("twine upload dist/*")


@task
def run(c, level="INFO"):
    """run pykiso with dummy.yaml setup and loglevel INFO"""
    c.run("rm -f killme.log")
    c.run(f"pykiso -c examples/dummy.yaml --log-level={level} -l killme.log")


@task
def update_copyright(c):
    p = pathlib.Path(".")
    files = p.glob("**/*.py")

    # RST docs copyright notice
    pat = r":Copyright:.*?SPDX-License-Identifier: EPL-[0-9.]+\s"
    cp_doc_pat = re.compile(pat, re.MULTILINE + re.DOTALL)
    # comment copyright notice
    pat = r"#*\s*#\s*Copyright.*?#\s*SPDX-License-Identifier: EPL-[0-9.]+\s*#*\s+"
    cp_com_pat = re.compile(pat, re.MULTILINE + re.DOTALL)

    for pyf in files:
        with open(pyf, "r+") as f:
            text = f.read()
            text = cp_doc_pat.sub("", text, count=1)
            text = cp_com_pat.sub("", text, count=1)
            text = COPYRIGHT + text
            f.seek(0)
            f.write(text)
            f.truncate()
