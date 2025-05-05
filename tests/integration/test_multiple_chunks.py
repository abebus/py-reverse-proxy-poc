import os

import pytest
from aiohttp import ClientSession

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
@pytest.mark.parametrize(
    "data",
    [
        os.urandom(70_000),
        os.urandom(80_000),  # FIXME this fails
        #     os.urandom(256_000),
        #       os.urandom(1_000_000)
    ],
)
async def test_404_for_unrouted_path(proxy_server, data):
    url = "http://0.0.0.0:8080/test"

    async with ClientSession() as session:
        async with session.post(url, data=data) as resp:
            assert resp.status == 200
