import asyncio
import websockets
import json
from dotenv import find_dotenv, get_key
from src import encryption

LOOP = asyncio.get_event_loop()

async def find_user(username):
    env_path = find_dotenv()
    host = get_key(env_path, "HOST")
    port = get_key(env_path, "PORT")
    websocket_path = f"ws://{host}:{port}"

    async with websockets.connect(websocket_path) as websocket:
        msg = json.dumps(
            {
                "command": "find_user",
                "username": username
            }
        )
        await websocket.send(msg)
        json_user = await websocket.recv()
        return json.loads(json_user)

def login_coroutine(username, password):
    current_user = LOOP.run_until_complete(find_user(username))

    if encryption.verify_password(password, current_user["password_hash"]):
        return current_user
    else:
        return False
