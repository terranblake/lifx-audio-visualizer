
from typing import List, Tuple
import lifxlan


class LifxLightChanger:
    def __init__(self, expected_number_of_lights: int = None, verbose=True):
        self.expected_number_of_lights = expected_number_of_lights
        self.lifx = lifxlan.LifxLAN()
        self.verbose = verbose
        self.devices: List[lifxlan.MultiZoneLight] = []

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

    def change_to_red(self):
        # Dummy function for testing client/server
        self.safe_change_light_color(lifxlan.RED)

    def change_to_blue(self):
        # Dummy function for testing client/server
        self.safe_change_light_color(lifxlan.BLUE)
