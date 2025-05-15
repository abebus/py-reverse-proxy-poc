from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable
from weakref import WeakSet

from httptools import HttpRequestParser, parse_url

from config import load_routes

if TYPE_CHECKING:
    from route_trie import Target


class UpStreamReaderProtocol(asyncio.StreamReaderProtocol):
    __slots__ = ()

    proxy: "ReverseProxy" | None = None

    def data_received(
        self,
        data: bytes,
        __super_call=asyncio.StreamReaderProtocol.data_received,  # bytecode opt
    ):
        __super_call(self, data=data)
        self.proxy.write(data)

    def eof_received(self, __super_call=asyncio.StreamReaderProtocol.eof_received):
        self.proxy.upstream_done()
        return __super_call(self)


class ReverseProxy:
    # region Init

    logger = logging.getLogger(__name__)

    __slots__ = (
        "transport",
        "upstream_transport",
        "req_parser",
        "path",
        "should_keep_alive",
        "target",
        "__buf",
    )

    __response_404 = (
        b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __response_502 = (
        b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __route_trie = load_routes()
    _tasks: WeakSet[asyncio.Task] = WeakSet()
    _loop = asyncio.get_event_loop()

    def __init__(
        self,
        bytearray=bytearray,  # bytecode opt
        HttpRequestParser=HttpRequestParser,  # bytecode opt
    ):
        self.req_parser = HttpRequestParser(self)
        self.req_parser.set_dangerous_leniencies(
            lenient_keep_alive=True, lenient_data_after_close=True
        )
        self.should_keep_alive: bool = False
        self.__buf: bytearray = bytearray()
        self.upstream_transport: asyncio.Transport | None = None
        self.path: str | None = None
        self.target: Target | None = None

    # endregion

    # region asyncio.Protocol callbacks

    def connection_made(self, transport: asyncio.Transport):  # type: ignore
        self.logger.debug("Connection established: %s", transport)
        self.transport = transport

    def connection_lost(
        self, exc: Exception | None = None
    ):  # TODO: handle Connection: close properly
        if exc:
            self.logger.warning("Connection lost with error: %s", exc, exc_info=True)
        else:
            self.logger.debug("Connection closed cleanly")

        if self.transport and not self.transport.is_closing():
            self.transport.close()
            self.transport = None

        if self.upstream_transport and not self.upstream_transport.is_closing():
            self.upstream_transport.close()
            self.upstream_transport = None

    def data_received(
        self,
        data: bytes,
    ):
        if self.upstream_transport and not self.__buf:
            self.upstream_transport.write(data)
        else:
            self.__buf.extend(data)
        self.req_parser.feed_data(data)

    def eof_received(self):
        if self.upstream_transport:
            self.upstream_transport.write_eof()

    # endregion

    # region HttpRequestParser callbacks

    def on_url(
        self,
        url: bytes,
        parse_url: Callable[[bytes], object] = parse_url,  # bytecode opt
        len: Callable[[object], int] = len,  # bytecode opt
    ):
        self.path = parse_url(url).path
        self.logger.debug("Parsed URL path: %s", self.path)
        match = self.__route_trie.match(self.path)

        if not match:
            self.logger.info("No route matched for path %s, returning 404", self.path)
            self.write(self.__response_404)
            self.connection_lost()
            return

        key, target = match
        self.target = target

        if key == self.path:
            return

        key_position = self.__buf.find(key)
        self.logger.debug("Curr buf is %s", self.__buf)
        if key_position != -1:
            self.__buf = (
                self.__buf[:key_position] + self.__buf[key_position + len(key) :]
            )  # remove added path from req to backend
            self.logger.debug("Modifying buffer to %s", self.__buf)

    def on_headers_complete(self):
        self.should_keep_alive = self.req_parser.should_keep_alive()
        self.logger.debug(f"{self.should_keep_alive=} {self.transport}")

        t = self._loop.create_task(self.route_and_pipe())
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    # endregion

    # region Internal methods

    def write(self, data):
        if self.transport and not self.transport.is_closing():
            self.transport.write(data)

    def upstream_done(self):
        self.logger.debug("Upstream finished sending data (EOF)")
        if not self.should_keep_alive:
            self.connection_lost()

    async def route_and_pipe(
        self,
        ConnectionError=ConnectionError,  # bytecode opt
        bytes=bytes,  # bytecode opt
        UpStreamReaderProtocol=UpStreamReaderProtocol,  # bytecode opt
        asyncio=asyncio,  # bytecode opt
    ):
        try:
            self.logger.debug("Connection to %s:%s", self.target.host, self.target.port)
            if self.upstream_transport is None or self.upstream_transport.is_closing():
                (
                    self.upstream_transport,
                    upstream_proto,
                ) = await self._loop.create_connection(
                    lambda: UpStreamReaderProtocol(
                        asyncio.StreamReader(loop=self._loop), loop=self._loop
                    ),
                    self.target.host.decode(),
                    self.target.port.decode(),
                )
                upstream_proto.proxy = self

            self.upstream_transport.write(bytes(self.__buf))
            self.__buf.clear()

        except ConnectionError as exc:
            self.logger.error("Failed to connect to upstream: %s", exc, exc_info=True)
            self.write(self.__response_502)
            self.connection_lost()
