#!/usr/bin/env python3
import os
from websockets.sync.client import connect
from src import console


if __name__ == "__main__":
    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    # TODO: Make sure the server is using tls.
    with connect("ws://localhost:8765") as websocket:
        ui = console.Console(websocket)
        ui.run()
