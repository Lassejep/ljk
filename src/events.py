import asyncio
import websockets
from dotenv import find_dotenv, get_key
from src import encryption

def login_coroutine(username, password):
    env_path = find_dotenv()
    host = get_key(env_path, "HOST")
    port = get_key(env_path, "PORT")
    websocket_path = f"ws://{host}:{port}"

    async def find_user(username):
        async with websockets.connect(websocket_path) as websocket:
            await websocket.send("find_user")
            await websocket.send(username)
            username = await websocket.recv()
            id = await websocket.recv()
            password_hash = await websocket.recv()
            encrypted_symmetrical_key = await websocket.recv()
        return {
            "username": username,
            "id": id,
            "password_hash": password_hash,
            "encrypted_symmetrical_key": encrypted_symmetrical_key
        }

    current_user = asyncio.get_event_loop().run_until_complete(
        find_user(username)
    )

    if encryption.verify_password(password, current_user["password_hash"]):
        return current_user
    else:
        return False
