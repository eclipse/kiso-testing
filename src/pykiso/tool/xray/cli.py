import getpass
import os
import tempfile
from xml.etree.ElementTree import ElementTree

import click

from .xray import add_case_results, extract_test_results


@click.group()
@click.option(
    "--user",
    help="Xray user id",
    required=True,
    default=None,
    hide_input=True,
)
@click.option(
    "--password",
    help="Valid Xray API key (if not given ask at command prompt level)",
    required=False,
    default=None,
    hide_input=True,
)
@click.option(
    "--url",
    help="URL of Xray server",
    required=True,
)
@click.pass_context
def cli_xray(ctx: dict, user: str, password: str, url: str) -> None:
    """Xray interaction tool."""
    ctx.ensure_object(dict)
    ctx.obj["USER"] = user or input("Enter Client ID Xray and Press enter:")
    ctx.obj["PASSWORD"] = password or getpass.getpass("Enter your password and Press ENTER:")
    ctx.obj["URL"] = url


@cli_xray.command("upload")
@click.option(
    "--test-execution-id",
    help="Test execution ticket ID to import the JUnit xml test results",
    required=False,
    default=None,
    type=click.STRING,
)
@click.option(
    "-r",
    "--path-results",
    help="full path to the folder containing the JUNIT reports",
    type=click.Path(exists=True, resolve_path=True),
    required=True,
)
@click.pass_context
def cli_upload(
    ctx,
    path_results: str,
    test_execution_id: str,
) -> None:
    """Upload the JUnit xml test results on xray."""
    # From the JUnit xml files, create a temporary file to keep only the results marked with an xray decorator.
    for file in os.listdir(path_results):
        if file.endswith(".xml"):
            tree = ElementTree()
            tree.parse(file)
            root = tree.getroot()
            for testsuite in root.findall("testsuite"):
                testcase = testsuite.find("testcase")
                properties = testcase.find("properties")
                if properties is None:
                    tree.getroot().remove(testsuite)
                    continue
                is_test_key = False
                for property in properties.findall("property"):
                    if property.attrib.get("name") == "test_key":
                        # breakpoint()
                        is_test_key = True
                        break
                if not is_test_key:
                    print("delete")
                    tree.getroot().remove(testsuite)

            with tempfile.TemporaryFile() as fp:
                tree.write(fp)
                fp.seek(0)
                xml_results = fp.read().decode()

    # def extract_test_results(path_results: str):
    #     ...

    # def publish_test_results():
    #     ...

    # update the new created run with case statuses
    test_results = add_case_results(
        base_url=ctx.obj["URL"],
        user=ctx.obj["USER"],
        password=ctx.obj["PASSWORD"],
        results=xml_results,
        test_execution_id=test_execution_id,
    )
    print(test_results)
