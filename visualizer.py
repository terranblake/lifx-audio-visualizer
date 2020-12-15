import numpy as np
import colorsys
import subprocess
from lifxlan.utils import RGBtoHSBK


class MicrophoneVisualizer():

    window_average = 0
    window = []
    peak = 0

    current_zones = []

    audio_volume = 0
    average_volume = 0

    # percent - 0 to 1
    beam_volume = 0

    def __init__(self, **kwargs):
        self.mapping_functions = {
            'static': self.__get_static_color_mapping,
            'gradient': self.__get_gradient_color_mapping,
            'palette': self.__get_palette_color_mapping,
        }
        self.mode = kwargs.get('mode', 'static')
        self.window_length = kwargs.get('window_length', 50)

        self.volume_smoothing = kwargs.get('volume_smoothing', 5)

        self.num_beams = kwargs.get('num_beams', 8)
        self.num_zones_per_beam = kwargs.get('num_zones_per_beam', 10)
        self.num_corner_pieces = kwargs.get('num_corner_pieces', 1)

        self.num_addressable_zones = (
            self.num_beams * self.num_zones_per_beam) + self.num_corner_pieces
        self.center_zone_offset = kwargs.get(
            'center_zone_offset',
            (self.num_beams * self.num_zones_per_beam) / 2)

    def on_data(self, data=None):
        if data is None:
            print('no data received when calling on_data')
            return

        self.chunk_average = np.average(np.abs(data))
        chunk_average_peak = self.chunk_average * 2
        self.peak = chunk_average_peak

        if len(self.window) == self.window_length:
            self.window.pop(self.window_length - 1)

        self.window.insert(0, self.peak)
        self.window_average = np.average(self.window)

        self.audio_volume = int(50 * self.peak / 2 ** 14)
        self.average_volume = int(50 * self.window_average / 2 ** 14)

        smoothing_values = self.window[:self.volume_smoothing]
        smoothing_values.append(self.chunk_average)
        smoothed_chunk = (sum(smoothing_values) / 2) / len(smoothing_values)
        self.beam_volume = round(smoothed_chunk / self.window_average, 2)

        if self.beam_volume > 1:
            self.beam_volume = 1

    def get_color_mapping(self):
        self.current_zones = self.mapping_functions[self.mode]()
        return self.current_zones

    def __get_static_color_mapping(self):
        num_left_lit = int(self.beam_volume * self.center_zone_offset)
        num_right_lit = int(self.beam_volume * (self.num_addressable_zones - self.center_zone_offset))
        num_left_unlit = self.center_zone_offset - num_left_lit
        num_right_unlit = (self.num_addressable_zones - self.center_zone_offset) - num_right_lit

        unlit_color = RGBtoHSBK((0, 0, 0), 0)
        lit_color = RGBtoHSBK((127, 0, 127), 500)

        left_unlit = [unlit_color] * num_left_unlit
        left_lit = [lit_color] * num_left_lit
        right_lit = [lit_color] * num_right_lit
        right_unlit = [unlit_color] * num_right_unlit

        mapping = left_unlit + left_lit + right_lit + right_unlit
        device_display = ''.join([' ' if x[-1] == 0 else '*' for x in mapping])

        subprocess.call('clear')
        print(f'[{device_display}]')
        print(("-" * self.audio_volume) + "|")
        print((" " * self.average_volume) + "|")

        return mapping


    def __get_gradient_color_mapping(self):
        '''uses the gradient argument to pick colors based on the location of each segment of the gradient'''
        pass

    def __get_palette_color_mapping(self):
        '''uses the palette argument to assign colors based on a static list of colors'''
        pass