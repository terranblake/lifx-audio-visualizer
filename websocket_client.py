#!/usr/bin/env python3
import asyncio
import json
import lifxlan
import numpy as np
import websockets
import pyaudio


class WSClient:
    def __init__(self):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk_size = 4096
        self.websocket = None

    def start(self):
        asyncio.get_event_loop().run_until_complete(self.connect_and_run())

    async def establish_connection_to_server(self, ip='127.0.0.1', port=8080):
        self.websocket = await websockets.connect(f'ws://{ip}:{port}', ping_interval=None)

    async def connect_and_run(self, ip='127.0.0.1', port=8080):
        websocket_url = f'ws://{ip}:{port}'
        print(f'Initializing connection to {websocket_url}')
        await self.establish_connection_to_server(ip, port)
        print(f'Connected to {websocket_url}')

        print('Attempting to open audio stream')
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format, channels=self.channels, rate=self.rate,
                        frames_per_buffer=self.chunk_size, input=True)
        print('Audio stream opened')
        last_color = None
        while True:
            try:
                data = np.frombuffer(stream.read(self.chunk_size), dtype=np.int16)
                peak = np.average(np.abs(data)) * 2
                bars = int(50 * peak / 2 ** 16)
                command = {
                    'command': 'change_color'
                }
                if bars > 0:
                    command['color'] = lifxlan.BLUE
                else:
                    command['color'] = lifxlan.RED

                if command['color'] != last_color:
                    await self.websocket.send(json.dumps(command))
                    last_color = command['color']
            except websockets.ConnectionClosedError:
                print('Lost connection to server, attempting to reconnect')
                await self.establish_connection_to_server(ip, port)
                print('Reconnected')


        # Test command
        # await websocket.send(json.dumps({
        #     'command': 'change_color',
        #     'color': lifxlan.GOLD
        # }))


if __name__ == '__main__':
    ws_client = WSClient()
    ws_client.start()
