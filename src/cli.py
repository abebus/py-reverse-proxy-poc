import argparse
import asyncio

from protocol import serve


def main():
    parser = argparse.ArgumentParser(description="Start the reverse proxy server.")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to listen on (default: 8080)"
    )

    args = parser.parse_args()

    # Pass args to serve

    try:
        asyncio.run(serve(args.host, args.port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    from .logging import setup_logging
    setup_logging()
    main()
