from protocols.base import ReverseProxyBase

class HttpReverseProxy(ReverseProxyBase):
    
    __response_404 = (
        b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __response_502 = (
        b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    __route_trie = load_routes()
    
    def data_received(
        self,
        data: bytes,
    ):
        if self.upstream_transport and not self.__buf:
            self.upstream_transport.write(data)
        else:
            self.__buf.extend(data)
        self.req_parser.feed_data(data)

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