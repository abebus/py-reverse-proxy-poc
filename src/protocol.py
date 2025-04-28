import asyncio
from typing import cast

import uvloop

# from config import load_routes # TODO trie in cython?

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class ReverseProxy(asyncio.Protocol):
    __slots__ = ("transport", "url", "buffer", "_response_404")

    transport: asyncio.Transport
    url: bytes

    def __init__(self):
        self.buffer = b""
        self._response_404 = b"HTTP/1.1 404 Not Found"
        # self._route_trie = load_routes()

    def connection_made(self, transport: asyncio.BaseTransport):
        print("conn made")
        self.transport = cast(asyncio.Transport, transport)

    def data_received(self, data: bytes):
        # print(f"data recieved {data}")
        self.url = data[data.index(b"/") : data.index(b"HTTP")]
        asyncio.create_task(self.route_and_pipe())

    async def route_and_pipe(self):
        print("route_and_pipe")
        path = self.url.split(b"?", 1)[0]  # ignore query string
        print(f"pipe to {path}")
        # TODO: implement
        # target = self._route_trie.match(path)

        # if not target:
        #     # Return 404
        #     self.transport.write(self._response_404)
        #     self.transport.close()
        #     return

        try:
            reader, writer = await asyncio.open_connection(path)
            writer.write(self.buffer)
            await writer.drain()
            asyncio.create_task(self.pipe_response(reader))
        except Exception as e:
            print(f"Failed to connect to upstream: {e}")
            self.transport.close()

    async def pipe_response(self, reader: asyncio.StreamReader):
        print("pipe_response")
        try:
            while not reader.at_eof():
                chunk = await reader.read(65536)
                if not chunk:
                    break
                self.transport.write(chunk)
        finally:
            self.transport.close()


async def serve():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: ReverseProxy(), "0.0.0.0", 8080)
    print("Reverse proxy running at http://localhost:8080")
    await server.serve_forever()
