#!/usr/bin/env python3
import json
from collections import defaultdict
from typing import Dict, Union
import asyncio
import websockets


class WSDashboard:
    def __init__(self, verbose=True):
        self.server = None
        self.clients = []
        self.subscriptions = {}
        self.current_color = None
        self.verbose = verbose
        self.loop = asyncio.get_event_loop()

    async def setup_event_loop(self):
        tasks = [
            # asyncio.create_task(self.broadcast()),
            asyncio.create_task(self.serve())
        ]
        await asyncio.wait(tasks)

    async def log(self, msg: str):
        if self.verbose:
            print(f'WSServer: {msg}')

    def start(self, ip='127.0.0.1', port=8080):
        # Set IP to 0.0.0.0 if you want clients from separate devices to be able to connect
        print(f'Listening at {ip}:{port}')
        self.server = websockets.serve(self.handler, ip, port, ping_interval=None, ping_timeout=None)
        self.loop.run_until_complete(self.server)
        self.loop.run_forever()


    async def handle_message(self, websocket, message: str) -> Union[None, Dict]:
        message = json.loads(message)
        command = message['command']

        if command == f'microphone_output' and 'microphone' in self.subscriptions:
            for sub in self.subscriptions['microphone']:
                await sub.send(json.dumps(message))
        elif command == 'microphone':
            if command in list(self.subscriptions.keys()):
                self.subscriptions[command].append(websocket)
            else:
                self.subscriptions[command] = [websocket]
        return None

    async def handler(self, websocket, path):
        await self.log(f'Received connection')
        self.clients.append(websocket)
        try:
            async for message in websocket:
                response = await self.handle_message(websocket, message)
                if response is not None:
                    websocket.send(json.dumps(response))
        except Exception as e:
            print(f'handler error {e}')

        await self.log(f'Client disconnected')
        self.clients.remove(websocket)


if __name__ == '__main__':
    ws_server = WSDashboard()
    ws_server.start()
