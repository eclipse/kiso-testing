##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import click
import pytest
from click.testing import CliRunner

from pykiso import cli


@pytest.fixture()
def runner():
    return CliRunner()


def test_main(runner):
    runner.invoke(
        cli.main,
        [
            "pykiso",
            "-c",
            "examples/acroname.yaml",
            "-c",
            "examples/acroname.yaml",
        ],
    )


@pytest.mark.parametrize(
    "user_tags,expected_results",
    [
        (["--branch-level", "dev"], {"branch-level": ["dev"]}),
        (["--branch-level", "dev,master"], {"branch-level": ["dev", "master"]}),
        (
            ["--branch-level", "dev", "--variant", "delta"],
            {"branch-level": ["dev"], "variant": ["delta"]},
        ),
    ],
)
def test_eval_user_tags(user_tags, expected_results, mocker):
    click_context_mock = mocker.MagicMock()
    click_context_mock.args = user_tags
    user_tags = cli.eval_user_tags(click_context_mock)
    assert user_tags == expected_results


def test_eval_user_tags_empty(mocker):
    click_context_mock = mocker.MagicMock()
    click_context_mock.args = []
    user_tags = cli.eval_user_tags(click_context_mock)
    assert user_tags == {}


@pytest.mark.parametrize(
    "user_tags,expected_message",
    [
        (
            ["branch-level", "dev"],
            " branch-level",
        ),
        (
            ["--forbidden_underscore", "dev"],
            "--forbidden_underscore",
        ),
    ],
)
def test_eval_user_tags_exception_no_such_option(user_tags, expected_message, mocker):
    # user_tags = ["branch-level", "dev"]
    click_context_mock = mocker.MagicMock()
    click_context_mock.args = user_tags
    with pytest.raises(click.NoSuchOption) as exec_info:
        eval_user_tags = cli.eval_user_tags(click_context_mock)
    assert expected_message in exec_info.value.format_message()


def test_eval_user_tags_exception_bad_option_usage(mocker):
    click_context_mock = mocker.MagicMock()
    click_context_mock.args = ["--branch-level"]
    with pytest.raises(click.BadOptionUsage) as exec_info:
        eval_user_tags = cli.eval_user_tags(click_context_mock)
    assert "tag --branch-level" in exec_info.value.format_message()
