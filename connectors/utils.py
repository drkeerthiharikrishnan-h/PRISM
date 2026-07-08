"""Shared HTTP retry utilities for all connectors."""
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

_RETRYABLE_STATUS = frozenset((429, 500, 502, 503, 504))


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError))


http_retry = retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)


@http_retry
async def retryable_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    r = await client.get(url, **kwargs)
    if r.status_code in _RETRYABLE_STATUS:
        r.raise_for_status()
    return r


@http_retry
async def retryable_post(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    r = await client.post(url, **kwargs)
    if r.status_code in _RETRYABLE_STATUS:
        r.raise_for_status()
    return r
