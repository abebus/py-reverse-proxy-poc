import asyncio
import multiprocessing

import pytest
import pytest_asyncio
import uvloop
from aiohttp import web

multiprocessing.set_start_method("spawn", force=True)

pytestmarkasyncio = pytest.mark.asyncio


@pytest.fixture(scope="session", autouse=True)
def proxy_logging():
    from rp_logging import setup_logging

    setup_logging()
    return


@pytest.fixture(scope="session", autouse=True)
def event_loop_policy():
    return uvloop.EventLoopPolicy()


def _run_server_in_process():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        from protocol import ReverseProxy
        from rp_logging import setup_logging

        setup_logging()

        server = await loop.create_server(
            ReverseProxy, "127.0.0.1", 8080, start_serving=False
        )
        async with server:
            await server.serve_forever()

    loop.run_until_complete(run())


@pytest_asyncio.fixture(scope="session")
async def proxy_server():  # FIXME idk why and how but with pytest-asyncio `server.serve_forever()` blocks entire event loop
    """Start the reverse proxy server."""
    proc = multiprocessing.Process(target=_run_server_in_process, daemon=True)
    proc.start()

    await asyncio.sleep(0.5)

    yield

    proc.join(timeout=1)
    if proc.is_alive():
        proc.terminate()


@pytest_asyncio.fixture(scope="session")
async def upstream_server():  # TODO? make separate binary upstream (mb in go) and call it from `subprocess`?
    """Start a dummy upstream server."""

    async def echo_handler(request):
        response = web.StreamResponse(status=200)
        response.content_type = "application/octet-stream"
        await response.prepare(request)

        async for chunk in request.content.iter_chunked(65536):
            await response.write(chunk)

        await response.write_eof()

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", echo_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 9999)
    await site.start()

    yield
    await runner.cleanup()
