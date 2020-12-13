
import json
from collections import defaultdict
from typing import Optional
import asyncio
import websockets

from .lifx_changer import LifxLightChanger


class WSServer:
    def __init__(self, verbose=True):
        self.server = None
        self.lifx = LifxLightChanger(1)

        self.clients = []
        self.client_message_counts = defaultdict(int)

        self.verbose = verbose

    async def log(self, msg: str):
        if self.verbose:
            print(f'WSServer: {msg}')

    def start(self, ip='127.0.0.1', port=8080):
        await self.log('Initializing connection to lights')
        self.lifx.initialize()

        # Set IP to 0.0.0.0 if you want clients from separate devices to be able to connect
        self.server = websockets.serve(self.handler, ip, port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    async def handle_message(self, message: str) -> Optional[Dict]:
        message = json.loads(message)
        command = message['command']
        if command == 'change_color':
            color = message['color']
            await self.log(f'Changing color to {color}')
            self.lifx.safe_change_light_color(color)

    async def handler(self, websocket, path):
        print(f'Received connection')
        self.clients.append(websocket)

        async for message in websocket:
            self.client_message_counts[websocket] += 1
            response = await self.handle_message(message)
            if response is not None:
                websocket.send(json.dumps(response))

        print(f'Client disconnected')
        self.clients.remove(websocket)


if __name__ == '__main__':
    ws_server = WSServer()
    ws_server.start()
