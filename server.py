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

# Setup websockets
async def handler(websocket, path):
    async for command in websocket:
        match command:
            case "connect":
                print(f"{HOST}:{PORT} < Connected")
                await websocket.send(f"{HOST}:{PORT} > Connected")
            case "add_user":
                username = await websocket.recv()
                password_hash = await websocket.recv()
                encrypted_symmetrical_key = await websocket.recv()
                db.add_user(username, password_hash, encrypted_symmetrical_key)
                print(f"{HOST}:{PORT} < add_user {username}")
                await websocket.send(f"{HOST}:{PORT} > User Added")
            case "add_service":
                service_user_name = await websocket.recv()
                service_name = await websocket.recv()
                service_encrypted_password = await websocket.recv()
                service_notes = await websocket.recv()
                user_id = await websocket.recv()
                db.add_service(
                    service_user_name,
                    service_name,
                    service_encrypted_password,
                    service_notes,
                    user_id,
                )
                print(f"{HOST}:{PORT} < add_service {user_name} {service_name}")
                await websocket.send(f"{HOST}:{PORT} > Service Added")
            case "delete_service":
                service_id = await websocket.recv()
                db.delete_service(service_id)
                print(f"{HOST}:{PORT} < delete_service {service_id}")
                await websocket.send(f"{HOST}:{PORT} > Service Deleted")
            case "delete_user":
                user_id = await websocket.recv()
                db.delete_user(user_id)
                print(f"{HOST}:{PORT} < delete_user {user_id}")
                await websocket.send(f"{HOST}:{PORT} > User Deleted")
            case "find_user":
                username = await websocket.recv()
                print(f"{HOST}:{PORT} < find_user {username}")
                user = db.find_user(username)
                username = user["username"]
                id = str(user["id"])
                encrypted_symmetrical_key = user["encrypted_symmetrical_key"]
                password_hash = user["password_hash"]
                await websocket.send(username)
                await websocket.send(id)
                await websocket.send(password_hash)
                await websocket.send(encrypted_symmetrical_key)
            case "find_user_services":
                user_id = await websocket.recv()
                print(f"{HOST}:{PORT} < find_user_services {user_id}")
                services = db.find_user_services(user_id)
                await websocket.send(json.dumps(services))
            case _:
                print(f"{HOST}:{PORT} < Unknown Command {command}")
                await websocket.send(f"{HOST}:{PORT} > Unknown Command")

start_server = websockets.serve(handler, HOST, PORT)

asyncio.get_event_loop().run_until_complete(start_server)
print(f"server running on {HOST}:{PORT}")

asyncio.get_event_loop().run_forever()
print(f"server on {HOST}:{PORT} stopped")
