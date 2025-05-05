from aiohttp import ClientSession

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
async def test_404_for_unrouted_path(proxy_server):
    url = "http://0.0.0.0:8080/nonexistent"

    async with ClientSession() as session:
        async with session.get(url) as resp:
            assert resp.status == 404
            text = await resp.text()
            assert text == ""
