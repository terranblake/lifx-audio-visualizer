
from typing import Dict, List, Tuple
import lifxlan
import subprocess

import time
import datetime as dt
from timer import Timer


class LifxLightChanger:
    def __init__(self, verbose=True):
        self.lifx = lifxlan.LifxLAN()
        self.verbose = verbose
        self.devices: List[lifxlan.MultiZoneLight] = []
        self.device_color_zone_counts: Dict[lifxlan.MultiZoneLight, int] = {}
        self.device_color_mapping: Dict[str, list] = {}

        # Messing with gradients based on moving average of volume
        self.current_gradient_colors = []
        self.current_gradient_value = 0
        self.device_timers: Dict[lifxlan.MultiZoneLight, Timer] = {}

    def log(self, msg: str):
        if self.verbose:
            print(f'LifxLightChanger: {msg}')

    def initialize(self):
        self.log('Attempting to find lights...')
        counter = 0
        while True:
            try:
                counter += 1
                devices: List[lifxlan.Light] = self.lifx.get_multizone_lights()
                if len(devices) > 0:
                    break
            except lifxlan.WorkflowException:
                pass
        self.log(f'Found {len(devices)} lights. Took {counter} requests')

        # Convert lights to multizone
        for i in range(len(devices)):
            devices[i] = lifxlan.MultiZoneLight(devices[i].mac_addr, devices[i].ip_addr, source_id=devices[i].source_id)
        self.devices = devices

        self.log(f'Converted {len(devices)} lights to MultiZoneLights')

        # Get count of color zones
        self.log('Getting color zones')
        for device in self.devices:
            color_zones = self.get_color_zones(device, safe=True)
            self.device_color_zone_counts[device] = len(color_zones)
            self.device_color_mapping[device] = color_zones
            self.device_timers[device] = Timer(name=device.label)
            self.change_color(color=lifxlan.utils.RGBtoHSBK((0, 0, 0), 0))

    @staticmethod
    def get_color_zones(device: lifxlan.MultiZoneLight, start=None, end=None, safe=True):
        if safe:
            while True:
                try:
                    zones = device.get_color_zones(start=start, end=end)
                    return zones
                except lifxlan.WorkflowException:
                    pass
        else:
            return device.get_color_zones(start=start, end=end)

    def change_color(self, color: Tuple[int, int, int, int], safe=False):
        """

        :param color:
        :param safe: If safe is true, will call self.safe_change_light_color,
        which will guarantee the color change occurs
        :return:
        """
        for device in self.devices:
            if safe:
                self.safe_change_light_color(color)
            else:
                device.set_color(color, rapid=True)

    def safe_change_light_color(self, color: Tuple[int, int, int, int]):
        for device in self.devices:
            while True:
                try:
                    device.set_color(color)
                    break
                except lifxlan.WorkflowException:
                    pass

    def set_color_zones(self, zones_values: list, safe=False):
        # gradient_value should be a value from 0 to 1

        for device in self.devices:
            # does this device need to be rate-limited?
            if self.device_timers[device].is_limited(ops=20, ms=1000):
                continue

            for x in range(len(zones_values)):
                previous_color = self.device_color_mapping[device][x]
                new_color = zones_values[x]

                if previous_color == new_color:
                    continue
                
                self.device_timers[device].step()
                self.device_color_mapping[device][x] = new_color

                try:
                    device.set_zone_color(x, x + 1, new_color, rapid=not safe, apply=1)
                except lifxlan.WorkflowException as e:
                    print(e)
                    continue