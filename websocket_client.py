#!/usr/bin/env python3
import asyncio
import json
import lifxlan
from time import sleep
import numpy as np
from datetime import datetime
import sys
import websockets
import pyaudio

import weighting
from visualizer import MicrophoneVisualizer


class WSClient:
    clients = []
    subscriptions = {}

    stream = None
    reconnect_delay = 3

    def __init__(self, mode: str = 'static', safe: int = 0, port=8080, device_name=None, palette_name=None):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk_size = 1024
        self.websocket = None
        self.dashboard = None
        self.mode = mode
        self.safe = safe
        self.port = port
        self.device_name = device_name
        self.visualizer = MicrophoneVisualizer(
            color_palette_name=palette_name,
            mode=self.mode,
            volume_smoothing=10,
            window_length=200,
            num_beams=6,
            num_zones_per_beam=10,
            num_corner_pieces=1,
            center_zone_offset=30,
            color_transition_interval=300,
            chunk_size=self.chunk_size,
            channels=self.channels,
            sampling_rate=self.rate,
            primary_color_percent=1.0,
            background_color_percent=0.3,
            effect=MicrophoneVisualizer.effects['NONE'])
        self.a_weighted_filter = weighting.ABC_weighting(curve='B')

    def start(self):
        # Important
        # done, pending = await asyncio.wait([listener_task, producer_task], return_when=asyncio.FIRST_COMPLETED)

        asyncio.get_event_loop().run_until_complete(
            self.connect_and_run(port=self.port))
        # asyncio.ensure_future(self.establish_connection_to_server('127.0.0.1', self.port))
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

    async def connect_and_run(self, ip='127.0.0.1', port=8080):
        while True:
            try:
                await self.establish_connection_to_server(ip, port)

                # if self.dashboard is None:
                #     await self.establish_connection_to_dashboard(ip, port + 1)

                print('Attempting to open audio stream')
                p = pyaudio.PyAudio()

                info = p.get_host_api_info_by_index(0)
                numdevices = info.get('deviceCount')
                selected_device = 0
                #for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
                for i in range(0, numdevices):
                    if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                        name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                        if self.device_name != None and self.device_name.lower() in name.lower():
                            selected_device = i

                devinfo = p.get_device_info_by_index(selected_device)
                print("Selected device is ", devinfo.get('name'))
                if p.is_format_supported(
                        self.rate,  # Sample rate
                        input_device=devinfo["index"],
                        input_channels=devinfo['maxInputChannels'],
                        input_format=pyaudio.paInt16):
                    print(f"Selected device supports {self.rate}hz")

                self.stream = p.open(
                    input_device_index=selected_device,
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    frames_per_buffer=self.chunk_size,
                    input=True,
                    # stream_callback=self.process_stream_callback
                )

                print('Audio stream opened')

                while True:
                    await self.process_stream_callback(
                        self.stream.read(self.chunk_size))

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

    async def process_stream_callback(self, data):
        now = datetime.now()
        data = np.frombuffer(data, dtype=np.int16)

        # def process_stream_callback(self, in_data, frame_count, time_info, status):
        # data = np.frombuffer(in_data, dtype=np.int16)
        self.visualizer.on_data(data)

        message = {
            'command': 'set_color_zones',
            'zones_values': self.visualizer.get_color_mapping()
        }

        # for sending messages to the dashboard server
        # kinda janky
        # if len(self.visualizer.frequency) == 0 or len(self.visualizer.power) == 0:
        #     return

        # message = {
        #     'command': 'microphone_output',
        #     'data': {
        #         'frequency':
        #         self.visualizer.frequency.astype(int).tolist(),
        #         'power': [
        #             int(x / (10 ^ 9)) for x in weighting.A_weight(
        #                 self.visualizer.power, self.rate).tolist()
        #         ],
        #         'power': self.visualizer.power.tolist(),
        #         'streamReadAt':
        #         str((int(now.timestamp()) * 1000) + int(now.microsecond / 1e3))
        #     }
        # }

        if self.websocket:
            await self.websocket.send(json.dumps(message))
        return (None, pyaudio.paContinue)


if __name__ == '__main__':
    visualizer_mode = sys.argv[1]
    safe = int(sys.argv[2])
    port = int(sys.argv[3])
    device = sys.argv[4]
    palette_name = sys.argv[5]

    ws_client = WSClient(mode=visualizer_mode, safe=safe, port=port, device_name=device, palette_name=palette_name)
    ws_client.start()