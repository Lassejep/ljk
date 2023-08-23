import websockets
import asyncio

async def hello():
    async with websockets.connect("ws://localhost:8765") as websocket:
        message = input("Enter your message: ")
        await websocket.send(message)
        response = await websocket.recv()
        print(response)

asyncio.get_event_loop().run_until_complete(hello())
