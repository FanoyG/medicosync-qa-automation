from typing import Protocol
import httpx
from tenacity import (
    AsyncRetrying, retry_if_exception_type,
    retry_if_result, stop_after_attempt,
    wait_fixed,
)

RETRY_STATUS = {429, 502, 503, 504}
def _is_bad_status(response):
    return response.status_code in RETRY_STATUS

def _return_last_result(state):
    assert state.outcome is not None
    return state.outcome.result()

def _make_retrying(attempts: int):
    return AsyncRetrying(
        retry=retry_if_exception_type(httpx.TimeoutException) | retry_if_result(_is_bad_status),
        stop=stop_after_attempt(attempts),
        wait=wait_fixed(1),
        retry_error_callback= _return_last_result,
    )


class HttpClient(Protocol):
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response: ...

class RequestBuilder:
    def __init__(self, client: HttpClient):
        self.client = client
        self.path = ""
        self.json_body = None
        self.query_params = None
        self.path_params = None
        self.id = None
        self.timeout = 5.0
        self.headers = None
        self.retries = None

    def set_path(self, path: str):
        if not path:
            raise ValueError("set_path() needs a real path like \"/users\"")
        self.path = path
        return self
    
    def set_json(self, body: dict):
        if body is None:
            raise ValueError("set_json() needs a body, like {'name': 'John'}")
        self.json_body = body
        return self

    def set_params(self, params: dict):
        if params is None:
            raise ValueError("set_params() needs a dict, like {'page': 2}")
        self.query_params = params
        return self

    def set_id(self, id: int):
        if id is None:
            raise ValueError("set_id() needs an Int id, like \"2\"")
        self.id = id
        return self

    def set_timeout(self, seconds):
        self.timeout = seconds
        return self

    def set_headers(self, headers):
        self.headers = headers
        return self

    def set_retries(self, attempts: int):
        self.retries = attempts
        return self
    
    async def send(self, method="GET"):
        target_path = self.path
        if self.id is not None:
            target_path += f"/{self.id}"

        kwargs = {
            "params" : self.query_params,
            "json": self.json_body,
            "headers" : self.headers,
        }

        if self.timeout is not None:
            kwargs["timeout"] = self.timeout

        if self.retries is None or method != "GET":
            return await self.client.request(method, target_path, **kwargs)

        retrying = _make_retrying(attempts=self.retries)
        return await retrying(self.client.request, method, target_path, **kwargs)