#!/usr/bin/env python3
import asyncio
import json
import lifxlan
from time import sleep
import numpy as np
import sys
import websockets
import pyaudio
from visualizer import MicrophoneVisualizer


class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj,
                      (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32,
                       np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray, )):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def make_iter():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    def put(*args):
        loop.call_soon_threadsafe(queue.put_nowait, args)

    async def get():
        while True:
            yield await queue.get()

    return get(), put


class WSClient:
    clients = []
    subscriptions = {}

    stream = None
    reconnect_delay = 3

    def __init__(self, mode: str = 'static', safe: int = 0, port=8080):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk_size = 1024
        self.websocket = None
        self.dashboard = None
        self.mode = mode
        self.safe = safe
        self.port = port
        self.visualizer = MicrophoneVisualizer(mode=self.mode,
                                               volume_smoothing=10,
                                               window_length=400,
                                               num_beams=6,
                                               num_zones_per_beam=10,
                                               num_corner_pieces=1,
                                               center_zone_offset=5,
                                               color_transition_interval=300,
                                               chunk_size=self.chunk_size,
                                               channels=self.channels,
                                               sampling_rate=self.rate,
                                               primary_color_percent=0.5,
                                               background_color_percent=0.5)

    def start(self):
        # Important
        # done, pending = await asyncio.wait([listener_task, producer_task], return_when=asyncio.FIRST_COMPLETED)

        asyncio.get_event_loop().run_until_complete(self.connect_and_run(port=self.port))
        asyncio.ensure_future(self.establish_connection_to_dashboard('127.0.0.1', self.port))
        asyncio.get_event_loop().run_forever()

    async def establish_connection_to_server(self, ip='127.0.0.1', port=8080):
        print(f'Initializing connection to {ip}:{port}')
        try:
            self.websocket = await websockets.connect(f'ws://{ip}:{port}',
                                                      ping_interval=None,
                                                      ping_timeout=None)
        except ConnectionRefusedError as err:
            print('Unable to connect to server')
            print(err)
            return

        print(f'Connected to server at {ip}:{port}')

    async def establish_connection_to_dashboard(
            self, ip='127.0.0.1', port=8080) -> websockets.WebSocketServer:
        print(f'Initializing ws server at {ip}:{port}')
        self.dashboard = await websockets.serve(self.handler,
                                                ip,
                                                port,
                                                ping_interval=None,
                                                ping_timeout=None)
        print(f'Server available at {ip}:{port}')
        return self.dashboard

    async def connect_and_run(self, ip='127.0.0.1', port=8080):
        # while True:
        try:
            # if self.websocket is None:
            #     await self.establish_connection_to_server(ip, port)

            # if self.dashboard is None:
            #     await self.establish_connection_to_dashboard(ip, port + 1)

            print('Attempting to open audio stream')
            p = pyaudio.PyAudio()
            self.stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                frames_per_buffer=self.chunk_size,
                input=True
            )

            print('Audio stream opened')

            while True:
                await self.process_stream()
        except websockets.ConnectionClosedError:
            print('Lost connection to server, attempting to reconnect')
        except websockets.exceptions.InvalidStatusCode:
            print(
                f'Server is unavailable, sleeping for {self.reconnect_delay} seconds'
            )
            await asyncio.sleep(self.reconnect_delay)
        except Exception as e:
            print(e, type(e))
            # break

        print('Done!')

    async def process_stream(self):
        data = np.frombuffer(self.stream.read(self.chunk_size), dtype=np.int16)
        message = {
            'data': list(data)
        }

        formatted = json.dumps(message, cls=NumpyEncoder)
        # print(list(data)[:5])
        if len(self.clients) > 0:
            for client in self.clients:
                await client.send(formatted)

        # print(f'Stream callback called')
        return (data, pyaudio.paContinue)

    async def handler(self, websocket: websockets.WebSocketServerProtocol,
                      path):
        print(f'Received connection')
        self.clients.append(websocket)
        try:
            async for message in websocket:
                response = await self.handle_message(websocket, message)
                if response is not None:
                    websocket.send(json.dumps(response))
        except Exception as e:
            print(e)

        print(f'Client disconnected')
        self.clients.remove(websocket)

    async def handle_message(self, websocket, message: str):
        message = json.loads(message)
        command = message['command']

        print(f'websocket subscribing to {command}')

        if command == 'get_frequency_data':
            return self.


if __name__ == '__main__':
    visualizer_mode = sys.argv[1]
    safe = int(sys.argv[2])
    port = int(sys.argv[3])

    ws_client = WSClient(mode=visualizer_mode, safe=safe, port=port)
    ws_client.start()