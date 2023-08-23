import websockets
import asyncio
from src.database import Database

PORT = 8765
HOST = "localhost"

# Setup database
db = Database(data.db)
db.add_users_table()
db.add_services_table()

# database interactions
async def add_user(websocket, path):
    async for message in websocket:
        if message == "add_user":
            await websocket.send("Enter username: ")
            username = await websocket.recv()
            await websocket.send("Enter password: ")
            password = await websocket.recv()
            await websocket.send("Enter email: ")
            email = await websocket.recv()
            db.add_user(username, password, email)

# Setup websockets
async def echo(websocket, path):
    async for message in websocket:
        await websocket.send(f"{HOST}:{PORT}> {message}")

start_server = websockets.serve(echo, HOST, PORT)

asyncio.get_event_loop().run_until_complete(start_server)
print(f"server running on {HOST}:{PORT}")

asyncio.get_event_loop().run_forever()
print(f"server on {HOST}:{PORT} stopped")
