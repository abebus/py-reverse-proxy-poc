import pytest
from aiohttp import ClientSession

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
@pytest.mark.parametrize(
    "method", ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
)
async def test_methods_through_proxy(proxy_server, upstream_server, method):
    url = "http://127.0.0.1:8080/test"
    headers = {"X-Test-Header": method}
    data = "payload" if method in ["POST", "PUT", "PATCH"] else None

    async with ClientSession() as session:
        async with session.request(method, url, headers=headers, data=data) as resp:
            assert resp.status == 200
            body = await resp.text()
            if method != "HEAD":
                assert resp.method == method
                if data:
                    assert body == data
