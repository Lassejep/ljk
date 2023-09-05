#!/usr/bin/env python3
from os import path
from dotenv import load_dotenv, find_dotenv, set_key
from src import gui, encryption

if not path.exists(".env"):
    open(".env", "a").close()
    load_dotenv(find_dotenv())
    set_key(find_dotenv(), "PORT", "8765")
    set_key(find_dotenv(), "HOST", "localhost")

window = gui()
window.run()
