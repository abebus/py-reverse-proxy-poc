import asyncio
import pathlib
import subprocess

import pytest
import pytest_asyncio
import uvloop

pytestmarkasyncio = pytest.mark.asyncio(scope="session")


@pytest_asyncio.fixture(autouse=True)
def proxy_logging():
    from rp_logging import setup_logging

    setup_logging()
    return


@pytest_asyncio.fixture(scope="session")
def event_loop():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def proxy_server():
    """Start the reverse proxy server."""
    loop = asyncio.get_running_loop()

    from protocol import ReverseProxy

    server = await loop.create_server(
        ReverseProxy, "127.0.0.1", 8080, start_serving=False
    )
    async with server:
        t = asyncio.create_task(server.serve_forever())
        await asyncio.sleep(0.1)

        yield server  # expose object to locals for debug

        t.cancel()


@pytest_asyncio.fixture()
async def upstream_server():
    """Start a dummy upstream server using an external binary."""

    process = subprocess.Popen(
        [str(pathlib.Path(__file__).parent.parent.parent / "bin" / "echo_server")]
    )

    await asyncio.sleep(0.1)

    assert process.poll() is None, "Echo server failed to start"

    yield

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
