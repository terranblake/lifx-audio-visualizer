#!/usr/bin/env python

import pyaudio
import socket
import sys
import numpy as np
from lifxlan import BLUE, GREEN, LifxLAN, MultiZoneLight, Light, Device

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096

named_devices = {}
zones = {}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio = pyaudio.PyAudio()
# stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
s.connect(('', 4444))


try:
    while True: 
        original_data = s.recv(CHUNK)
        data = np.fromstring(original_data, dtype=np.int16)

        peak=np.average(np.abs(data))*2
        bars="#"*int(50*peak/2**16)
        print("%05d %s" % (peak, bars))
        # stream.write(original_data)
except KeyboardInterrupt:
    pass

print('Shutting down')
s.close()
stream.close()
audio.terminate()


def refresh_devices(num_lights = 1):
    num_lights = None

    # instantiate LifxLAN client, num_lights may be None (unknown).
    # In fact, you don't need to provide LifxLAN with the number of bulbs at all.
    # lifx = LifxLAN() works just as well. Knowing the number of bulbs in advance 
    # simply makes initial bulb discovery faster.
    print("Discovering lights...")
    lifx = LifxLAN(num_lights)

    # get devices
    lifx.get_devices()
    devices = lifx.devices

    for device in devices:
        name = device.get_label()
        print(name, 'found')
        named_devices[name] = device

def refresh_zones():
    for name, device in named_devices.items():
        if isinstance(device, MultiZoneLight):
            zones[name] = device.get_color_zones()


if __name__ == "__main__":
    refresh_devices()
    refresh_zones()