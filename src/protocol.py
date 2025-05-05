import asyncio
import logging
from typing import cast

from httptools import HttpRequestParser, parse_url

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
    if asyncio.get_event_loop_policy() is not uvloop.EventLoopPolicy:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class ReverseProxy(asyncio.Protocol):
    # region Init

    logger = logging.getLogger(__name__)

    __slots__ = ("transport", "parser", "path")

    __response_404 = (
        b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __response_502 = (
        b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __route_trie = load_routes()
    _tasks = set()
    _loop = asyncio.get_running_loop()

    def __init__(self):
        self.parser = HttpRequestParser(self)

    # endregion

    # region asyncio.Protocol callbacks

    def connection_made(self, transport: asyncio.BaseTransport):
        self.logger.debug("Connection established: %s", transport)
        self.transport = cast(asyncio.Transport, transport)

    def connection_lost(self, exc: Exception | None):
        if exc:
            self.logger.warning("Connection lost with error: %s", exc, exc_info=True)
        else:
            self.logger.debug("Connection closed cleanly")
        self.transport = None

    def data_received(self, data: bytes):
        self.parser.feed_data(data)
        self.logger.debug("Received data: %r", data)

        task = self._loop.create_task(self.route_and_pipe(data))
        task.add_done_callback(self._tasks.discard)
        self._tasks.add(task)

    # endregion

    # region HttpRequestParser callbacks

    def on_url(
        self,
        url: bytes,
        parse_url=parse_url,  # bytecode opt
    ):
        self.path = parse_url(url).path
        self.logger.debug("Parsed URL path: %s", self.path)

    # endregion

    # region Internal methods
    async def route_and_pipe(
        self,
        data: bytes,
        __open_connection=asyncio.open_connection,  # bytecode opt
    ):
        target = self.__route_trie.match(self.path)

        if not target:
            self.logger.info("No route matched for path %s, returning 404", self.path)
            self.transport.write(self.__response_404)
            self.transport.close()
            return

        try:
            upstream_reader, upstream_writer = await __open_connection(
                target.host.decode(), target.port.decode()
            )
            self.logger.info("Connected to upstream %s:%s", target.host, target.port)

            upstream_writer.write(data)
            await upstream_writer.drain()

            self.logger.debug("Sent request to upstream")

            await self.pipe_response(upstream_reader)

            upstream_writer.close()
            await upstream_writer.wait_closed()

        except Exception as exc:
            self.logger.error("Failed to connect to upstream: %s", exc, exc_info=True)
            self.transport.write(self.__response_502)

        if self.transport and not self.transport.is_closing():
            self.logger.debug("Closing transport to client")
            self.transport.close()

    async def pipe_response(
        self,
        reader: asyncio.StreamReader,
        len=len,  # bytecode opt
    ):
        try:
            while not reader.at_eof():
                chunk = await reader.read(65536)
                reader.feed_data
                if not chunk:
                    break
                self.logger.debug("Piping chunk of size %d bytes to client", len(chunk))
                self.transport.write(chunk)
        except Exception as exc:
            self.logger.error("Error while piping response: %s", exc, exc_info=True)
        finally:
            if self.transport and self.transport.can_write_eof():
                self.transport.write_eof()


async def serve(host="0.0.0.0", port=8080):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(ReverseProxy, host, port, start_serving=False)
    ReverseProxy.logger.info("Reverse proxy running at http://%s:%s", host, port)

    async with server:
        await server.serve_forever()
