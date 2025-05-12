import asyncio


async def serve(host="0.0.0.0", port=8080):
    from protocol import ReverseProxy

    loop = asyncio.get_event_loop()
    ReverseProxy._loop = loop
    server = await loop.create_server(ReverseProxy, host, port, start_serving=False)
    ReverseProxy.logger.info("Reverse proxy running at http://%s:%s", host, port)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(serve())
