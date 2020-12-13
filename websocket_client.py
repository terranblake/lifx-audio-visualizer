#!/usr/bin/env python3
import asyncio
import json
import lifxlan
import numpy as np
import websockets
import pyaudio


class WSClient:
    def __init__(self, mode: str = 'static'):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk_size = 4096
        self.websocket = None
        self.mode = mode
        self.mode_functions = {
            'static': self.mode_static,
            'gradient': self.mode_gradient,
        }

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
                await self.mode_functions[self.mode](stream)
                break
            except websockets.ConnectionClosedError:
                print('Lost connection to server, attempting to reconnect')
                await self.establish_connection_to_server(ip, port)
                print('Reconnected')

        print('Done!')

    # ===========================================
    # Mode functions
    #  - All Mode functions receive an audio stream as the argument.
    #  - When a Mode function returns, the runtime loop will end
    # ===========================================

    async def mode_static(self, stream: pyaudio.Stream):
        last_color = None
        while True:
            data = np.frombuffer(stream.read(self.chunk_size), dtype=np.int16)
            peak = np.average(np.abs(data)) * 2
            bars = int(50 * peak / 2 ** 16)

            command = {'command': 'change_color'}
            if bars > 0:
                command['color'] = lifxlan.BLUE
            else:
                command['color'] = lifxlan.RED
            if command['color'] != last_color:
                await self.websocket.send(json.dumps(command))
                last_color = command['color']

    async def mode_gradient(self, stream: pyaudio.Stream):
        # Set gradient colors
        await self.websocket.send({
            'command': 'set_gradient_colors',
            'colors': [lifxlan.RED, lifxlan.YELLOW]  # Currently supports exactly 2 colors
        })
        while True:
            # Terran: Put your code here, and decide when to send a gradient update
            # Command looks like this:
            # command = {
            #     'command': 'set_gradient_levels',
            #     'gradient': .5  # Gradient should be between 0 and 1
            # }
            # await self.websocket.send(json.dumps(command))
            pass


if __name__ == '__main__':
    ws_client = WSClient()
    ws_client.start()
