##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import shutil

import pytest

from pykiso.tool.testrail.extraction import JunitReport, Status

JUNIT_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
	<testsuite name="test_suite_1.MyTest1-1-1-20230103161804" tests="1" file="test_suite_1.py" time="0.021" timestamp="2023-01-03T16:18:04" failures="0" errors="0" skipped="0" test_ids="{&quot;VTestId&quot;: [&quot;129678&quot;, &quot;678543&quot;]}">
		<testcase classname="test_suite_1.MyTest1-1-1" name="test_run" time="0.021" timestamp="2023-01-03T16:18:04" file="examples\test_suite_1\test_suite_1.py" line="88">
			<!--In this case the default test_run method is overridden and
        instead of calling test_run from RemoteTest class the following
        code is called.
        Here, the test pass at the 3rd attempt out of 5. The setup and
        tearDown methods are called for each attempt.
        -->
		</testcase>
	</testsuite>
</testsuites>
"""

JUNIT_NO_TAG_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
	<testsuite name="test_suite_1.MyTest1-1-1-20230103161804" tests="1" file="test_suite_1.py" time="0.021" timestamp="2023-01-03T16:18:04" failures="0" errors="0" skipped="0">
		<testcase classname="test_suite_1.MyTest1-1-1" name="test_run" time="0.021" timestamp="2023-01-03T16:18:04" file="examples\test_suite_1\test_suite_1.py" line="88">
			<!--In this case the default test_run method is overridden and
        instead of calling test_run from RemoteTest class the following
        code is called.
        Here, the test pass at the 3rd attempt out of 5. The setup and
        tearDown methods are called for each attempt.
        -->
		</testcase>
	</testsuite>
</testsuites>
"""


@pytest.fixture(scope="function")
def create_junit_report(tmp_path):
    report = tmp_path / f"junit_run.xml"
    report.write_text(JUNIT_CONTENT)
    return tmp_path


@pytest.fixture(scope="function")
def create_junit_wihtout_tag_test_ids(tmp_path):
    report = tmp_path / f"junit_no_tag.xml"
    report.write_text(JUNIT_NO_TAG_CONTENT)
    return tmp_path


def test_ids_tag_extraction(create_junit_report):
    results = JunitReport.extract(create_junit_report)
    assert ("129678", Status.PASSED) in results
    assert ("678543", Status.PASSED) in results


def test_ids_tag_extraction_notag(create_junit_wihtout_tag_test_ids):
    results = JunitReport.extract(create_junit_wihtout_tag_test_ids)
    assert results == []
