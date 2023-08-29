import websockets
import asyncio
import json
from dotenv import find_dotenv, load_dotenv, get_key
from src.database import Database
from src.utils import setup_server

setup_server()

ENV_PATH = find_dotenv()
HOST = get_key(ENV_PATH, "HOST")
PORT = get_key(ENV_PATH, "PORT")

db = Database("data.db")

async def handler(websocket, path):
    async for json_msg in websocket:
        msg = json.loads(json_msg)
        match msg["command"]:
            case "connect":
                print(f"{HOST}:{PORT} < Connected")
                await websocket.send(f"{HOST}:{PORT} > Connected")

            case "find_user":
                username = msg["username"]
                print(f"{HOST}:{PORT} < find_user {username}")
                user = db.find_user(username)
                await websocket.send(json.dumps(user))

            case "search_user_services":
                username = msg["username"]
                service_name = msg["service_name"]
                print(
                    f"{HOST}:{PORT} < "
                    f"search_user_services {username} {service_name}"
                )
                service_list = db.search_user_services(username, service_name)
                await websocket.send(json.dumps(service_list))

            case "find_user_services":
                username = msg["username"]
                print(f"{HOST}:{PORT} < find_user_services {username}")
                service_list = db.find_user_services(username)
                await websocket.send(json.dumps(service_list, indent=4))

            case _:
                print(f"{HOST}:{PORT} < Unknown Command {command}")
                await websocket.send(f"{HOST}:{PORT} > Unknown Command")

start_server = websockets.serve(handler, HOST, PORT)

asyncio.get_event_loop().run_until_complete(start_server)
print(f"server running on {HOST}:{PORT}")

asyncio.get_event_loop().run_forever()
print(f"server on {HOST}:{PORT} stopped")
