import multiprocessing
import asyncio
import websockets
from multiprocessing import Queue
import threading
import torch
HOST='127.0.0.1'
PORT = 8192

def getwork(q):
    # def getworkthread(q):

    @asyncio.coroutine
    def hello(websocket, path):
        name = yield from websocket.recv()
        if name.startswith('longlive'):
            while 1:
                if not q.empty():
                    yield from websocket.send(q.get())
                else:
                    yield from websocket.send('empty queue...')
                    # asyncio.sleep(.6)
        else:
            print(f"< recvied {name}")
            if name is not None:
                if not q.empty():
                    q.get_nowait()
                q.put(name)


        print(f'the queue size is : {q.qsize()}')

    start_server = websockets.serve(hello, HOST,PORT)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    # t1=threading.Thread(target=getworkthread,args=(q,))
    # t2 = threading.Thread(target=getworkthread, args=(q,))
    # t1.start()
    # t2.start()
    # t1.join()
    # t2.join()

q=Queue(maxsize=1)

p1=multiprocessing.Process(target=getwork,args=(q,))
p1.start()


torch.save()