import asyncio
from typing import cast

from config import load_routes

try:
    import uvloop
except ImportError:
    import warnings

    warnings.warn(
        "uvloop is not installed. Falling back to the default asyncio event loop.\n"
        "For better performance, consider installing uvloop: pip install uvloop",
        RuntimeWarning,
    )
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class ReverseProxy(asyncio.Protocol):
    __slots__ = (
        "transport",
        "url",
        "buffer",
        "_response_404",
        "_response_502",
        "_route_trie",
    )

    transport: asyncio.Transport
    url: bytes

    def __init__(self):
        self.buffer = b""
        self._response_404 = (
            b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        )
        self._response_502 = (
            b"HTTP/1.1 502 Bad Gateway\r\n"
            b"Content-Length: 0\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )
        self._route_trie = load_routes()

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = cast(asyncio.Transport, transport)

    def data_received(self, data: bytes):
        self.url = data[data.index(b"/") : data.index(b"HTTP")]
        asyncio.create_task(self.route_and_pipe())

    async def route_and_pipe(self):
        path = self.url[: self.url.find(b"?")]  # ignore query string
        target = self._route_trie.match(path)

        if not target:
            self.transport.write(self._response_404)
            self.transport.close()
            return

        try:
            reader, writer = await asyncio.open_connection(
                target.host.decode(), target.port.decode()
            )
            writer.write(self.buffer)
            await writer.drain()
            await self.pipe_response(reader)
        except Exception as e:
            print(f"Failed to connect to upstream: {e}")
            self.transport.write(self._response_502)
            self.transport.close()

    async def pipe_response(self, reader: asyncio.StreamReader):
        print("pipe_response")
        try:
            while not reader.at_eof():
                print("start read")
                chunk = await asyncio.wait_for(reader.read(65536), timeout=3)
                print(chunk)
                if not chunk:
                    break
                self.transport.write(chunk)
        except asyncio.TimeoutError:
            print("Timeout reading response, assuming end of body.")
        finally:
            try:
                self.transport.write_eof()  # Ensure EOF is sent to the client
            except (AttributeError, ConnectionResetError):
                pass
            self.transport.close()


async def serve(host="0.0.0.0", port=8080):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: ReverseProxy(), host, port)
    print(f"Reverse proxy running at http://{host}:{port}")
    await server.serve_forever()
