from copy import deepcopy
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests

from nlpland.types import Url


class ApiClient(object):
    """Generic client to interact with a generic Rest API.

    Subclasses should implement functionality accordingly with the provided service methods, i.e.
    ``get``, ``post``, ``patch`` and ``delete``. It uses static methods to ``encode`` and ``decode``
    the data and calls the ``call_api`` method to make the actual call to the API. To retrive the
    status of the api it uses the``service_status`` function.
    """

    accept_type = "application/json"

    def __init__(
        self,
        base_url: Url,
        api_token: Optional[str] = None,
        status_endpoint: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialise client.

        Args:
            base_url (str): The base URL to the service being used.
            api_token (str): The token to authenticate with.
            status_endpoint (str): The endpoint to get current status of backend.
            timeout (int): Maximum time before timing out.
        """
        self.base_url = base_url
        self.api_token = api_token
        self.status_endpoint = urljoin(self.base_url, status_endpoint)
        self.timeout = timeout

    def get_auth_header(self) -> Dict[str, str]:
        """Returns parameters to be added to authenticate the request.

        This lives on its own to make it easier to re-implement it if needed.

        Returns:
            dict: A dictionary containing the credentials.
        """
        return {"Authorization": f"Bearer {self.api_token}"}

    def call_api(
        self,
        method: str,
        url: Url,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: int = None,
    ) -> Tuple[requests.Response, int]:
        """Call API.

        This returns object containing data, with error details if applicable.

        Args:
            method (str): The HTTP method to use.
            url (str): Resource location relative to the base URL.
            headers (dict or None): Extra request headers to set.
            params (dict or None): Query-string parameters.
            data (dict or None): Request body contents for POST or PATCH requests.
            files (dict or None: Files to be passed to the request.
            timeout (int): Maximum time before timing out.

        Returns:
            ResultParser or ErrorParser.
        """
        headers = deepcopy(headers) or {}
        headers["Accept"] = self.accept_type
        params = deepcopy(params) or {}
        data = data or {}
        files = files or {}
        r = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            files=files,
            data=data,
            timeout=timeout,
        )

        return r, r.status_code

    def get(
        self, url: Url, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[requests.Response, int]:
        """Call the API with a GET request.

        Args:
            url (Url): Resource location relative to the base URL.
            params (dict or None): Query-string parameters.
            **kwargs (Any): Extra arguments to pass to the request.

        Returns:
            ResultParser or ErrorParser.
        """
        return self.call_api("GET", url, params=params, **kwargs)

    def delete(
        self, url: Url, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[requests.Response, int]:
        """Call the API with a DELETE request.

        Args:
            url (str): Resource location relative to the base URL.
            params (dict or None): Query-string parameters.

        Returns:
            ResultParser or ErrorParser.
        """
        return self.call_api("DELETE", url, params=params, **kwargs)

    def patch(
        self,
        url: Url,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple[requests.Response, int]:
        """Call the API with a patch request.

        Args:
            url (str): Resource location relative to the base URL.
            params (dict or None): Query-string parameters.
            data (dict or None): Request body contents.
            files (dict or None: Files to be passed to the request.

        Returns:
            An instance of ResultParser or ErrorParser.
        """
        return self.call_api("PATCH", url, params=params, data=data, files=files, **kwargs)

    def put(
        self,
        url: Url,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple[requests.Response, int]:
        """Call the API with a PUT request.
        Args:
            url (str): Resource location relative to the base URL.
            params (dict or None): Query-string parameters.
            data (dict or None): Request body contents.
            files (dict or None: Files to be passed to the request.
        Returns:
            An instance of ResultParser or ErrorParser.
        """
        return self.call_api("PUT", url, params=params, data=data, files=files, **kwargs)

    def post(
        self,
        url: Url,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple[requests.Response, int]:
        """Call the API with a POST request.

        Args:
            url (str): Resource location relative to the base URL.
            params (dict or None): Query-string parameters.
            data (dict or None): Request body contents.
            files (dict or None: Files to be passed to the request.

        Returns:
            An instance of ResultParser or ErrorParser.
        """
        return self.call_api(
            method="POST", url=url, params=params, data=data, files=files, **kwargs
        )

    def service_status(self, **kwargs: Any) -> Tuple[requests.Response, int]:
        """Call the API to get the status of the service.

        Returns:
            An instance of ResultParser or ErrorParser.
        """
        return self.call_api("GET", self.status_endpoint, params={"format": "json"}, **kwargs)
