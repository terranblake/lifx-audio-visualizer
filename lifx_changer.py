
from typing import Dict, List, Tuple
import lifxlan


class LifxLightChanger:
    def __init__(self, expected_number_of_lights: int = None, verbose=True):
        self.expected_number_of_lights = expected_number_of_lights
        self.lifx = lifxlan.LifxLAN()
        self.verbose = verbose
        self.devices: List[lifxlan.MultiZoneLight] = []
        self.device_color_zone_counts: Dict[lifxlan.MultiZoneLight, int] = {}

        # Messing with gradients based on moving average of volume
        self.current_gradient_colors = []
        self.current_gradient_value = 0

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
            self.device_color_zone_counts[device] = len(self.get_color_zones(device, safe=True))

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

    def set_gradient_colors(self, colors: List[Tuple]):
        self.current_gradient_colors = colors

    def set_gradient_value(self, gradient_value: float, safe=False):
        # gradient_value should be a value from 0 to 1
        for device in self.devices:
            number_of_color_zones = self.device_color_zone_counts[device]
            color_zones = []
            for i in range(number_of_color_zones):
                if i / number_of_color_zones < gradient_value:
                    color_zones.append(self.current_gradient_colors[0])
                else:
                    color_zones.append(self.current_gradient_colors[1])
            device.set_zone_colors(color_zones, rapid=not safe)

    def set_color_zones(self, zones_values: list, safe=False):
        # gradient_value should be a value from 0 to 1
        off = [0, 0, 0, 0]
        for device in self.devices:
            color_zones = []
            for x in zones_values:
                if x == 0:
                    color_zones.append(off)
                else:
                    color_zones.append(lifxlan.RED)
            device.set_zone_colors(color_zones, rapid=not safe)