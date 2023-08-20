#!/usr/bin/env python3

from src import database, gui, utils
from os import path

if not path.exists("data.db") or not path.exists(".env"):
    utils.setup()

base_dir = path.dirname(path.abspath(__file__))
icon_path = base_dir + "/img/ljk.gif"
db = database("data.db")
window = gui(db, icon_path)
window.run()
