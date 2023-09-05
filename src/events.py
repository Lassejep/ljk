import asyncio
import websockets
import json
from dotenv import find_dotenv, get_key
from src import encryption

def generate_password():
    password = ''.join(
        choice(ascii_letters + digits + punctuation)
        for _ in range(password_length)
    )
    return password

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
async def create_user(websocket, email, master_password):
    verification_key = encryption.hash_password(master_password)
    salt = encryption.generate_salt()
    master_key = encryption.generate_key(master_password, salt)
    vault_key = encryption.generate_random_key()
    encrypted_vault_key = encryption.encrypt_key(master_key, vault_key)

    msg = json.dumps(
        {
            "command": "create_user",
            "email": email,
        }
    )
    await websocket.send(msg)
    await websocket.send(salt)
    await websocket.send(verification_key)
    await websocket.send(encrypted_vault_key)
    reply = await websocket.recv()
    return reply

@websocket_wrapper
async def verify_user(websocket, email, master_password):
    msg = json.dumps(
        {
            "command": "get_verification_key",
            "email": email
        }
    )
    await websocket.send(msg)
    verification_key = await websocket.recv()
    print(f"verification_key_type: {type(verification_key)}")
    if not verification_key:
        return False
    if not encryption.verify_password(master_password, verification_key):
        return False
    return True
