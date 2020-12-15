#!/usr/bin/env python3
import json
from collections import defaultdict
from typing import Dict, Union
import asyncio
import websockets

from lifx_changer import LifxLightChanger


class WSServer:
    def __init__(self, verbose=True):
        self.server = None
        self.lifx = LifxLightChanger(1)
        self.clients = []
        self.client_message_counts = defaultdict(int)
        self.current_color = None
        self.verbose = verbose

    async def log(self, msg: str):
        if self.verbose:
            print(f'WSServer: {msg}')

    def start(self, ip='127.0.0.1', port=8080):
        print('Initializing connection to lights')
        self.lifx.initialize()

        # Set IP to 0.0.0.0 if you want clients from separate devices to be able to connect
        print(f'Listening at {ip}:{port}')
        self.server = websockets.serve(self.handler, ip, port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    async def handle_message(self, message: str) -> Union[None, Dict]:
        message = json.loads(message)
        safe = True if int(message['safe']) == 1 else 0

        command = message['command']
        if command == 'change_color':
            color = message['color']
            if self.current_color == color:
                await self.log('Received request for same as current color')
            else:
                await self.log(f'Changing color to {color}')
                self.current_color = color
                self.lifx.change_color(color)
        elif command == 'set_gradient_colors':
            colors = message['colors']
            await self.log(f'Set gradient colors to {colors}')
            self.lifx.set_gradient_colors(colors)
        elif command == 'set_gradient_levels':
            gradient_percentage = message['gradient']
            await self.log(f'Setting gradient level to {gradient_percentage}')
            self.lifx.set_gradient_value(gradient_percentage, safe=safe)
        elif command == 'set_color_zones':
            zones_values = message['zones_values']
            if zones_values == None:
                return

            await self.log(f'Setting color zones values')
            self.lifx.set_color_zones(zones_values, safe=safe)

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
