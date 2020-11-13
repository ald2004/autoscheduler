import asyncio
import websockets
import uuid
import time
HOST='127.0.0.1'
PORT = 8192
async def hello(data):
    uri = f"ws://{HOST}:{PORT}"

    # async with websockets.connect("ws://127.0.0.1:53392/", ping_timeout=None) as websocket:
    while 1:
        async with websockets.connect(uri,ping_timeout=None) as websocket:
            #name = input("What's your name? ")
            name = uuid.uuid4().hex
            # name=data
            await websocket.send(name)
            print(f"> sending {name}")
            #greeting = await websocket.recv()
            #print(f"< {greeting}")
            time.sleep(.5)
asyncio.get_event_loop().run_until_complete(hello('*****'))