#!/usr/bin/env python3
import ssl
import websockets
import asyncio
import curses
import argparse
from src import console


def start(screen, host, port):
    asyncio.run(main(screen, host, port))


async def main(screen, host, port):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_cert = ssl.get_server_certificate((host, port))
    ssl_context.load_verify_locations(cadata=ssl_cert)

    async with websockets.connect(
        f"wss://{host}:{port}", ping_interval=None, ssl=ssl_context
    ) as websocket:
        await console.run(screen, websocket)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Password Manager Client")
    parser.add_argument(
        "-H", "--host",
        default="0.0.0.0",
        help="Host to connect to"
    )
    parser.add_argument(
        "-p", "--port",
        default=8765,
        help="Port to connect to"
    )
    args = parser.parse_args()

    curses.wrapper(start, args.host, args.port)
