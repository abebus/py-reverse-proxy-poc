import pytest
from aiohttp import ClientSession

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
@pytest.mark.parametrize(
    "data_size",
    [70_000, 80_000, 256_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000],
)
async def test_payload_size(proxy_server, upstream_server, data_size):
    data = data = b"x" * data_size
    url = "http://127.0.0.1:8080/test"

    async with ClientSession() as session:
        async with session.post(url, data=data) as resp:
            assert resp.status == 200
