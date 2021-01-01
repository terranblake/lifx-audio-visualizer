#!/usr/bin/env python3
import json
from collections import defaultdict
from typing import Dict, Union
import asyncio
import websockets
from concurrent.futures import ProcessPoolExecutor

from lifx_changer import LifxLightChanger


class WSServer:
    def __init__(self, verbose=True):
        self.server = None
        self.lifx = LifxLightChanger(2)
        self.clients = []
        self.client_message_counts = defaultdict(int)
        self.current_color = None
        self.verbose = verbose
        self.loop = asyncio.get_event_loop()

    async def setup_event_loop(self):
        tasks = [
            # asyncio.create_task(self.broadcast()),
            asyncio.create_task(self.serve())
        ]

        await asyncio.wait(tasks)

    async def serve(self, ip: str = '127.0.0.1', port: str = '8080'):                                                                                           
        server = await websockets.serve(self.handler, ip, port, ping_interval=None, ping_timeout=None)
        await server.wait_closed()

    async def log(self, msg: str):
        if self.verbose:
            print(f'WSServer: {msg}')

    def start(self, ip='127.0.0.1', port=8080):
        print('Initializing connection to lights')
        self.lifx.initialize()

        # Set IP to 0.0.0.0 if you want clients from separate devices to be able to connect
        print(f'Listening at {ip}:{port}')
        # asyncio.get_event_loop().create_task(self.broadcast)
        # asyncio.get_event_loop().run_until_complete(self.server)
        self.loop.run_until_complete(self.setup_event_loop())
        self.loop.run_forever()


    async def handle_message(self, message: str) -> Union[None, Dict]:
        message = json.loads(message)
        command = message['command']
        if command == 'change_color':
            color = message['color']
            if self.current_color == color:
                await self.log('Received request for same as current color')
            else:
                await self.log(f'Changing color to {color}')
                self.current_color = color
                self.lifx.change_color(color)
        elif command == 'set_color_zones':
            zones_values = message['zones_values']
            if zones_values == None:
                return

            # await self.log(f'Setting color zones values')
            self.lifx.set_color_zones(zones_values)

    async def handler(self, websocket, path):
        await self.log(f'Received connection')
        self.clients.append(websocket)
        try:
            async for message in websocket:
                self.client_message_counts[websocket] += 1
                response = await self.handle_message(message)
                if response is not None:
                    websocket.send(json.dumps(response))
        except Exception as e:
            print(e)

        await self.log(f'Client disconnected')
        self.clients.remove(websocket)


if __name__ == '__main__':
    ws_server = WSServer()
    ws_server.start()
