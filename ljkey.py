#!/usr/bin/env python3
import ssl
import websockets
import asyncio
import curses
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
        ui = console.Console(websocket)
        while True:
            await ui.run()

if __name__ == "__main__":
    curses.wrapper(asyncio.run(main()))
