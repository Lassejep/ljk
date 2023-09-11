import asyncio
import websockets
import json
from dotenv import find_dotenv, get_key
from src import encryption, db

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
    encrypted_vault_key = encryption.encrypt(master_key, vault_key)

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
    user_id = int(await websocket.recv())
    database = db.Vault(user_id)
    encrypted_vault = encryption.encrypt_file(
        vault_key, f"TEMP/vault_{user_id}.db"
    )
    await websocket.send(encrypted_vault)

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
    if not verification_key:
        return False
    if not encryption.verify_password(master_password, verification_key):
        return False
    return True

@websocket_wrapper
async def get_vault(websocket, email, master_password):
    if not await verify_user(email, master_password):
        raise Exception("Invalid credentials")
    msg = json.dumps(
        {
            "command": "get_id",
            "email": email
        }
    )
    await websocket.send(msg)
    user_id = int(await websocket.recv())
    msg = json.dumps(
        {
            "command": "get_salt",
            "email": email
        }
    )
    await websocket.send(msg)
    salt = await websocket.recv()
    master_key = encryption.generate_key(
        master_password, salt
    )
    msg = json.dumps(
        {
            "command": "get_vault_key",
            "email": email
        }
    )
    await websocket.send(msg)
    encrypted_vault_key = await websocket.recv()
    vault_key = encryption.decrypt(master_key, encrypted_vault_key)
    msg = json.dumps(
        {
            "command": "get_vault",
            "user_id": user_id
        }
    )
    await websocket.send(msg)
    encrypted_vault = await websocket.recv()
    encrypted_vault = encryption.decrypt(vault_key, encrypted_vault)
    with open(f"TEMP/vault_{user_id}.db", "wb") as f:
        f.write(encrypted_vault)
    return db.Vault(user_id)

@websocket_wrapper
async def update_vault(websocket, email, master_password, vault):
    if not await verify_user(email, master_password):
        raise Exception("Invalid credentials")
    msg = json.dumps(
        {
            "command": "get_id",
            "email": email
        }
    )
    await websocket.send(msg)
    user_id = int(await websocket.recv())
    msg = json.dumps(
        {
            "command": "get_salt",
            "email": email
        }
    )
    await websocket.send(msg)
    salt = await websocket.recv()
    master_key = encryption.generate_key(
        master_password, salt
    )
    msg = json.dumps(
        {
            "command": "get_vault_key",
            "email": email
        }
    )
    await websocket.send(msg)
    encrypted_vault_key = await websocket.recv()
    vault_key = encryption.decrypt(master_key, encrypted_vault_key)
    msg = json.dumps(
        {
            "command": "update_vault",
            "user_id": user_id
        }
    )
    await websocket.send(msg)
    encrypted_vault = encryption.encrypt_file(
        vault_key, f"TEMP/vault_{user_id}.db"
    )
    await websocket.send(encrypted_vault)
