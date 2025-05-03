import asyncio
from typing import cast

from httptools import HttpRequestParser

from config import load_routes

try:
    import uvloop
except ImportError:
    import warnings

    warnings.warn(
        "uvloop is not installed. Falling back to default asyncio event loop.",
        RuntimeWarning,
    )
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class ReverseProxy(asyncio.Protocol):
    __slots__ = (
        "transport",
        "url",
        "parser",
        "target",
        "upstream_writer",
        "upstream_reader",
        "message_complete",
        "preconnect_buffer",
        "upstream_ready",
        "_response_404",
        "_response_502",
        "_route_trie",
    )

    def __init__(self):
        self.parser = HttpRequestParser(self)
        self._response_404 = (
            b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        )
        self._response_502 = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        self._route_trie = load_routes()
        self.target = None
        self.upstream_writer = None
        self.upstream_reader = None
        self.preconnect_buffer = []
        self.upstream_ready = asyncio.Event()

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = cast(asyncio.Transport, transport)

    def data_received(self, data: bytes):
        self.parser.feed_data(data)

        if self.upstream_ready.is_set():
            self.upstream_writer.write(data)
            asyncio.create_task(self.upstream_writer.drain())
        else:
            self.preconnect_buffer.append(data)

    def on_url(self, url: bytes):
        self.url = url

    def on_message_complete(self):
        asyncio.create_task(self.route_and_pipe())

    async def route_and_pipe(self):
        path = self.url.split(b"?", 1)[0]
        self.target = self._route_trie.match(path)

        if not self.target:
            self.transport.write(self._response_404)
            self.transport.close()
            return

        try:
            self.upstream_reader, self.upstream_writer = await asyncio.open_connection(
                self.target.host.decode(), self.target.port.decode()
            )

            # Flush early data
            for chunk in self.preconnect_buffer:
                self.upstream_writer.write(chunk)
            await self.upstream_writer.drain()
            self.preconnect_buffer.clear()

            self.upstream_ready.set()

            asyncio.create_task(self.pipe_response(self.upstream_reader))
        except Exception as e:
            print(f"[!] Failed to connect to upstream: {e}")
            self.transport.write(self._response_502)
            self.transport.close()

    async def pipe_response(self, reader: asyncio.StreamReader):
        try:
            while not reader.at_eof():
                chunk = await asyncio.wait_for(reader.read(65536), timeout=3)
                if not chunk:
                    break
                self.transport.write(chunk)
        except asyncio.TimeoutError:
            print("[!] Timeout while reading response")
        finally:
            try:
                self.transport.write_eof()
            except (AttributeError, ConnectionResetError):
                pass
            self.transport.close()


async def serve(host="0.0.0.0", port=8080):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: ReverseProxy(), host, port)
    print(f"Reverse proxy running at http://{host}:{port}")
    await server.serve_forever()
