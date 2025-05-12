import asyncio

import pytest
from aiohttp import ClientSession

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
@pytest.mark.parametrize(
    "concurrency", [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
)
async def test_concurrent_requests(proxy_server, upstream_server, concurrency):
    url = "http://127.0.0.1:8080/test"

    async def make_request(session):
        async with session.get(url) as resp:
            assert resp.status == 200

    async with ClientSession() as session:
        results = await asyncio.gather(
            *(make_request(session) for _ in range(concurrency))
        )

    assert len(results) == concurrency
