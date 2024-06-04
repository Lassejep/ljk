#!/usr/bin/env python3
import ssl
import websockets
import asyncio
from src import console
import pathlib


async def main():
    # TODO: Use a real certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
    ssl_context.load_verify_locations(localhost_pem)

    async with websockets.connect(
        "wss://localhost:8765", ssl=ssl_context, ping_interval=None
    ) as websocket:
        await console.start(websocket)

if __name__ == "__main__":
    asyncio.run(main())
