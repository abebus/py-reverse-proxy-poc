import asyncio

from aiohttp import ClientSession, TCPConnector

from integration.utils import count_open_connections

from .conftest import pytestmarkasyncio


@pytestmarkasyncio
async def test_keep_alive_basic(proxy_server, upstream_server):
    url = "http://127.0.0.1:8080/test/echo-json"

    # Get initial connection count
    initial_conn_count = count_open_connections()
    session_connector = None

    async with ClientSession() as session:
        # First request - should establish connection
        async with session.get(url, headers={"Connection": "keep-alive"}) as resp:
            assert resp.status == 200
            body = await resp.json()
            assert body["headers"].get("Connection", "")[0].lower() == "keep-alive"

            # Verify new connection was established
            assert count_open_connections() == initial_conn_count + 1
            first_conn = session.connector

        # Connection should persist after first request
        assert count_open_connections() == initial_conn_count + 1

        # Second request - should reuse connection
        async with session.get(url) as resp:
            assert resp.status == 200
            # Verify same connection was reused
            assert session.connector is first_conn
            assert count_open_connections() == initial_conn_count + 1

        assert not session.connector.closed
        session_connector = session.connector

    # After session closes, connection should be closed
    await asyncio.sleep(0.1)  # Allow time for connection closure
    assert session_connector.closed
    assert count_open_connections() == initial_conn_count


@pytestmarkasyncio
async def test_connection_close_header(
    proxy_server, upstream_server
):  # TODO: fails sometimes, find more robust way to ensure that TCP connections are closing
    url = "http://127.0.0.1:8080/test/echo-json"

    # Get initial connection count
    initial_conn_count = count_open_connections()

    async with ClientSession(
        connector=TCPConnector(limit=1, limit_per_host=1, force_close=True)
    ) as session1:
        # Request with explicit close
        async with session1.get(url, headers={"Connection": "close"}) as resp:
            # Connection should be closed after request
            assert count_open_connections() == initial_conn_count
            assert resp.status == 200
            body = await resp.json()
            assert body["headers"].get("Connection", "")[0].lower() == "close"

            # Verify connection was established
            first_conn = session1.connector

    # Give OS some time to refresh connections table
    await asyncio.sleep(0.3)

    initial_conn_count = count_open_connections()

    async with ClientSession(
        connector=TCPConnector(limit=1, limit_per_host=1, force_close=True)
    ) as session2:
        # Next request should create new connection
        async with session2.get(url) as resp:
            assert resp.status == 200
            await asyncio.sleep(0.3)
            # Verify new connection was established
            assert count_open_connections() == initial_conn_count
            assert session2.connector is not first_conn
            second_conn = session2.connector

    # Final connection cleanup
    await asyncio.sleep(0.1)
    assert first_conn.closed
    assert second_conn.closed
    assert count_open_connections() == initial_conn_count
