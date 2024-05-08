#!/usr/bin/env python3
import os
import ssl
import pathlib
import websockets
import asyncio
from src import console


async def main():
    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    # TODO: Use a real certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
    ssl_context.load_verify_locations(localhost_pem)

    async with websockets.connect(
        "wss://localhost:8765", ssl=ssl_context
    ) as websocket:
        ui = console.Console(websocket)
        await ui.run()

if __name__ == "__main__":
    asyncio.run(main())
