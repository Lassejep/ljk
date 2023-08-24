#!/usr/bin/env python3
from src import database, gui, encryption, utils
from os import path
from dotenv import find_dotenv, load_dotenv, get_key
import asyncio
import websockets

utils.setup_client()

window = gui()
window.run()
