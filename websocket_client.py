
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

    def start(self):
        asyncio.get_event_loop().run_until_complete(self.connect_and_run())

    async def connect_and_run(self, ip='127.0.0.1', port=8080):
        websocket_url = f'ws://{ip}:{port}'
        print(f'Initializing connection to {websocket_url}')
        async with websockets.connect(websocket_url) as websocket:
            print(f'Connected to {websocket_url}')

            print('Attempting to open audio stream')
            p = pyaudio.PyAudio()
            stream = p.open(format=self.format, channels=self.channels, rate=self.rate,
                            frames_per_buffer=self.chunk_size, input=True)
            last_color = None
            while True:
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
                    await websocket.send(json.dumps(command))
                    last_color = command['color']

            # Test command
            # await websocket.send(json.dumps({
            #     'command': 'change_color',
            #     'color': lifxlan.GOLD
            # }))


if __name__ == '__main__':
    ws_client = WSClient()
    ws_client.start()
