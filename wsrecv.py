import asyncio
import websockets
import uuid
import time

HOST='127.0.0.1'
PORT = 8192
async def hello():
    uri = f"ws://{HOST}:{PORT}"

    async with websockets.connect(uri,ping_timeout=None) as websocket:
        await websocket.send('longlive')
        while 1:
            # await websocket.send('receiver')

            name =  await websocket.recv()
            print(f"> recv {name}")
            # await asyncio.sleep(.5)
    # print('xxxxxx')
    # while 1:
    #     async with websockets.connect(uri) as websocket:
    #         await websocket.send('receiver')
    #         # await websocket.send('longlive')
    #         name =  await websocket.recv()
    #         print(f"> recv {name}")
    #     await asyncio.sleep(.5)
    #     print('xxxxxx')

asyncio.get_event_loop().run_until_complete(hello())