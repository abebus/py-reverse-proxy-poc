import asyncio
from integration.utils import count_open_connections
from aiohttp import ClientSession

from .conftest import pytestmarkasyncio

@pytestmarkasyncio
async def test_keep_alive_basic(proxy_server, upstream_server):
    url = "http://127.0.0.1:8080/test/echo-json"
    
    # Get initial connection count
    initial_conn_count = count_open_connections()
    
    async with ClientSession() as session:
        # First request - should establish connection
        async with session.get(url, headers={"Connection": "keep-alive"}) as resp:
            assert resp.status == 200
            print(url)
            print(resp.headers)
            print(await resp.read())
            body = await resp.json()
            assert body['headers'].get("Connection", "")[0].lower() == "keep-alive"
            
            # Verify new connection was established
            assert count_open_connections() == initial_conn_count + 1
            first_conn_id = id(session.connector)
        
        # Connection should persist after first request
        assert count_open_connections() == initial_conn_count + 1
        
        # Second request - should reuse connection
        async with session.get(url) as resp:
            assert resp.status == 200
            # Verify same connection was reused
            assert id(session.connector) == first_conn_id
            assert count_open_connections() == initial_conn_count + 1
    
    # After session closes, connection should be closed
    await asyncio.sleep(0.1)  # Allow time for connection closure
    assert count_open_connections() == initial_conn_count

@pytestmarkasyncio
async def test_connection_close_header(proxy_server, upstream_server):
    url = "http://127.0.0.1:8080/test/echo-json"
    
    # Get initial connection count
    initial_conn_count = count_open_connections()
    
    async with ClientSession() as session:
        # Request with explicit close
        async with session.get(url, headers={"Connection": "close"}) as resp:
            assert resp.status == 200
            assert resp.headers.get("Connection", "").lower() == "close"
            
            # Verify connection was established
            assert count_open_connections() == initial_conn_count + 1
            first_conn_id = id(session.connector)
        
        # Connection should be closed after request
        await asyncio.sleep(0.1)  # Allow time for connection closure
        assert count_open_connections() == initial_conn_count
        
        # Next request should create new connection
        async with session.get(url) as resp:
            assert resp.status == 200
            # Verify new connection was established
            assert count_open_connections() == initial_conn_count + 1
            assert id(session.connector) != first_conn_id
    
    # Final connection cleanup
    await asyncio.sleep(0.1)
    assert count_open_connections() == initial_conn_count