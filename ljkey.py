#!/usr/bin/env python3
import ssl
import websockets
import asyncio
import curses
from src import console
import pathlib


def start(screen):
    asyncio.run(main(screen))


async def main(screen):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
    ssl_context.load_verify_locations(localhost_pem)

    async with websockets.connect(
        "wss://localhost:8765", ssl=ssl_context, ping_interval=None
    ) as websocket:
        await console.run(screen, websocket)

if __name__ == "__main__":
    curses.wrapper(start)
