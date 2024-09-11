import base64
import concurrent.futures
import json
from enum import Enum
from typing import List, Tuple

import requests
import xmltodict


class ApiVersion(Enum):
    """Store all available Xray rest API versions."""

    #: Xray's V1 REST endpoint
    V1: str = "/rest/raven/1.0/"
    #: Xray's V2 REST endpoint
    V2: str = "api/v2/"


class ContentType(Enum):
    """Store all available header's content-type."""

    #: JSON content type
    JSON: str = "application/json"


class XrayApi:
    """Xray command API."""

    #: store the current API version in use
    API_VERSION: str = ApiVersion.V2.value

    @staticmethod
    def _construct_url(base_url: str, api_version: str, uri: str) -> str:
        """Construct the Xray url.

        :param base_url: Xray base url
        :param api_version: current api version in use
        :param uri: api command reference

        :return: request's url
        """
        return f"{base_url}/{api_version}{uri}" if not base_url.endswith("/") else f"{base_url}{api_version}{uri}"

    @staticmethod
    def get_token(url: str, user: str, password: str):
        client = {"client_id": user, "client_secret": password}

        token_result = requests.post(url=url, headers={"Content-Type": "application/json"}, json=client)
        token_json = token_result.json()

        return token_json

    @staticmethod
    def _construct_header(token: str, content_type: str) -> dict:
        """Construct the request header by adding content and authorization
        part.

        :param user: user id
        :param password: user's password or API key
        :param content_type: request's content type (json,...)

        :return: request's fulfilled header
        """
        print(f"token: {token}")
        headers = {"Authorization": "Bearer " + token}
        headers["Content-Type"] = "test/xml"
        return headers

    @classmethod
    def add_result_with_xml(
        cls,
        base_url: str,
        user: str,
        password: str,
        data: dict,
        test_execution_id: str | None = None,
    ) -> dict:
        # # 1 - get the correct token
        # construct url
        url_authenticate = cls._construct_url(base_url, cls.API_VERSION, uri="authenticate/")
        print(f"url_authenticate {url_authenticate}")
        token = cls.get_token(url_authenticate, user, password)

        # # 2 - import the data in xray
        # construct header
        headers = cls._construct_header(token, ContentType.JSON.value)
        print(f"headers {headers}")
        # requests.get url + header + data
        # uri = f"import/execution/junit/?" + "projectKey=BDU3" + "&testKey=" + project_id

        if test_execution_id is not None:
            uri = "import/execution/junit/?" + "projectKey=BDU3" + "&testExecKey=" + test_execution_id
        else:
            uri = "import/execution/junit/?" + "projectKey=BDU3"

        url = cls._construct_url(base_url, cls.API_VERSION, uri=uri)
        print(f"url {url}")
        print(f"data {data}")

        query_result = requests.post(url=url, headers=headers, data=data)
        print(f"query_result {query_result}")
        # new test result
        return json.loads(query_result.content)
