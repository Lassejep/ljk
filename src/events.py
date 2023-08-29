import asyncio
import websockets
import json
from dotenv import find_dotenv, get_key
from src import encryption

def websocket_wrapper(func):
    env_path = find_dotenv()
    host = get_key(env_path, "HOST")
    port = get_key(env_path, "PORT")
    websocket_path = f"ws://{host}:{port}"

    async def wrapper(*args, **kwargs):
        async with websockets.connect(websocket_path) as websocket:
            return await func(websocket, *args, **kwargs)

    return wrapper

@websocket_wrapper
async def find_user(websocket, username):
    msg = json.dumps(
        {
            "command": "find_user",
            "username": username
        }
    )
    await websocket.send(msg)
    json_user = await websocket.recv()
    return json.loads(json_user)

@websocket_wrapper
async def search_user_services(websocket, username, service_name):
    msg = json.dumps(
        {
            "command": "search_user_services",
            "username": username,
            "service_name": service_name
        }
    )
    await websocket.send(msg)
    json_services_list = await websocket.recv()
    return json.loads(json_services_list)

@websocket_wrapper
async def find_user_services(websocket, username):
    msg = json.dumps(
        {
            "command": "find_user_services",
            "username": username
        }
    )
    await websocket.send(msg)
    json_services_list = await websocket.recv()
    return json.loads(json_services_list)
