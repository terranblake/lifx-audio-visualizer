import numpy as np
import colorsys
import json
import subprocess
from lifxlan.utils import RGBtoHSBK
import random
import json
import datetime
import os
import struct
import numpy as np
from scipy.fftpack import rfft


class MicrophoneVisualizer():
    unlit_color = None
    lit_color = None
    palette = {}

    # historic frequency power levels
    power = []
    center_zone_update = 1

    frequency_ranges = [
        [16, 60, 'sub-bass', 'sb', '#F94144'],
        [60, 250, 'bass', 'b', '#F3722C'],
        [250, 500, 'low-mid', 'lm', '#F8961E'],
        [500, 2000, 'mid', 'm', '#F9C74F'],
        [2000, 4000, 'high-mid', 'hm', '#90BE6D'],
        [4000, 6000, 'low-high', 'lh', '#43AA8B'],
        [6000, 20000, 'high', 'h', '#577590'],
    ]

    effects = {
        'NONE': 'effects are disabled',
        'SCROLL': 'all zones wrap around to the next color; eventually wrapping to other lights',
        'PINGPONG': 'bounces the current color scheme from the current center to provide a moving effect',
    }

    frequency_windows_average = {}
    frequency_windows = {}
    frequency_window_length = 0
    frequency_volumes = {}

    window_average = 0
    window = []
    peak = 0

    current_zones = []

    audio_volume = 0
    average_volume = 0
    beam_volume = 0

    def __init__(self, **kwargs):
        self.color_palette_name = kwargs.get('color_palette', 'rainbow')
        self.get_color_palette()

        self.mapping_functions = {
            'static': self.__get_static_color_mapping,
            'gradient': self.__get_gradient_color_mapping,
            'palette': self.__get_palette_color_mapping,
        }
        self.sampling_rate = kwargs.get('sampling_rate')
        self.chunk_size = kwargs.get('chunk_size')
        self.channels = kwargs.get('channels')
        self.mode = kwargs.get('mode', 'static')
        self.window_length = kwargs.get('window_length', 50)
        self.frequency_window_length = kwargs.get('frequency_window_length', self.window_length)

        self.current_color = random.choice(list(self.palette.keys()))
        self.background_color = random.choice(list(self.palette.keys()))

        self.color_transition_interval = kwargs.get('color_transition_interval', 50)
        self.color_transition_count = self.color_transition_interval

        self.primary_color_percent = kwargs.get('primary_color_percent', 0.07)
        self.background_color_percent = kwargs.get('background_color_percent', 0.07)

        self.effect = kwargs.get('effect', self.effects['NONE'])

        self.volume_smoothing = kwargs.get('volume_smoothing', 5)

        self.num_beams = kwargs.get('num_beams', 8)
        self.num_zones_per_beam = kwargs.get('num_zones_per_beam', 10)
        self.num_corner_pieces = kwargs.get('num_corner_pieces', 1)

        self.num_addressable_zones = (
            self.num_beams * self.num_zones_per_beam) + self.num_corner_pieces
        self.center_zone_offset = kwargs.get(
            'center_zone_offset',
            (self.num_beams * self.num_zones_per_beam) // 2)
        self.current_center_offset = self.center_zone_offset

    def on_data(self, data=None):
        subprocess.call('clear')

        if data is None:
            print('no data received when calling on_data')
            return

        self.update_center_zone()
        power, _frequency = self.__convert_chunk_to_frequency_data(data)
        # self.__get_frequency_range_data(power)

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

        self.current_zones = self.mapping_functions[self.mode]()

    def update_center_zone(self):
        if self.effect == self.effects['NONE']:
            return

        # todo: this should be separate from color transition code
        current_zones = self.current_center_offset
        max_zones = self.num_addressable_zones
        
        if current_zones >= max_zones:
            if self.effect == self.effects['SCROLL']:
                self.current_center_offset = -1
                self.center_zone_update = 1
            else:
                self.center_zone_update = -1
        elif current_zones <= 0:
            self.center_zone_update = 1

        print(f'current {self.current_center_offset}\nupdate {self.center_zone_update}')
        self.current_center_offset += self.center_zone_update

    def __get_frequency_range_data(self, power):
        for range in self.frequency_ranges:
            if range[2] not in self.frequency_windows:
                self.frequency_windows[range[2]] = []

            if range[2] not in self.frequency_windows_average:
                self.frequency_windows_average[range[2]] = 1

            average = sum(power[range[0]:range[1]]) / (range[1] - range[0])

            if len(self.frequency_windows[range[2]]) == self.frequency_window_length:
                self.frequency_windows[range[2]].pop(self.frequency_window_length - 1)

            self.frequency_windows[range[2]].insert(0, average * 2)
            self.frequency_windows_average[range[2]] = np.average(self.frequency_windows[range[2]])

            smoothing_values = self.frequency_windows[range[2]][:self.volume_smoothing]
            smoothing_values.append(average)
            smoothed_chunk = (sum(smoothing_values) / 2) / len(smoothing_values)
            print(f'self.frequency_windows_average[range[2]] {range[2]}', self.frequency_windows_average[range[2]])
            self.frequency_volumes[range[2]] = round(smoothed_chunk / self.frequency_windows_average[range[2]], 2)

            # print(f'{range[2][:2]}\t- vol {self.frequency_volumes[range[2]]}')

            center = self.current_center_offset
            num_left_lit = int(self.frequency_volumes[range[2]] * center)
            num_right_lit = int(self.frequency_volumes[range[2]] * (self.num_addressable_zones - center))
            num_left_unlit = center - num_left_lit
            num_right_unlit = (self.num_addressable_zones - center) - num_right_lit

            left_unlit = [self.unlit_color] * num_left_unlit
            left_lit = [self.lit_color] * num_left_lit
            right_lit = [self.lit_color] * num_right_lit
            right_unlit = [self.unlit_color] * num_right_unlit

            print(f'{range[2]} {left_unlit} {left_lit} {right_lit} {right_unlit}')

            mapping = left_unlit + left_lit + right_lit + right_unlit
            device_display = ''.join([' ' if x != self.lit_color else '*' for x in mapping])
            print(f'{range[2][:2]}\t- vol {device_display}')
            

    def __convert_chunk_to_frequency_data(self, data):
        unpacked_data = struct.unpack(str(self.chunk_size * self.channels) + 'h', data)
        rfft_data = rfft(unpacked_data)
        abs_fourier_transform = np.abs(rfft_data)
        
        self.power = np.square(abs_fourier_transform)
        self.frequency = np.linspace(0, self.sampling_rate / 2, len(self.power))
        
        self.window.insert(0, self.peak)
        return self.power, self.frequency

    def get_color_palette(self):
        # colors = {
        #     'Red Salsa': RGBtoHSBK((249, 65, 68), 9000),
        #     'BLUE': [43634, 65535, 65535, 9000],
        # }
        palette_json = {}
        with open(f'{os.path.abspath(".")}/palettes/{self.color_palette_name}.json') as f:
            palette_json = json.load(f)

        # reset palette
        self.palette = {}
        for color in palette_json:
            self.palette[color['name']] = RGBtoHSBK(color['rgb'], 9000)
            
        return self.palette

    def get_color_mapping(self):
        return self.current_zones

    def __get_static_color_mapping(self):
        center = self.current_center_offset

        num_left_lit = int(self.beam_volume * center)
        num_right_lit = int(self.beam_volume * (self.num_addressable_zones - center))
        num_left_unlit = center - num_left_lit
        num_right_unlit = (self.num_addressable_zones - center) - num_right_lit

        # this whole color transition thing is garbage and is just for experimenting

        if self.color_transition_count >= self.color_transition_interval:
            self.color_transition_count = 0
            self.current_color = random.choice(list(self.palette.keys()))
            self.background_color = random.choice(list(self.palette.keys()))

            if self.current_color == self.background_color:
                self.current_color = random.choice(list(self.palette.keys()))

            self.unlit_color = list(self.palette[self.background_color])
            self.unlit_color[2] = int(self.background_color_percent * self.unlit_color[2])

            self.lit_color = list(self.palette[self.current_color])
            self.lit_color[2] = int(self.primary_color_percent * self.lit_color[2])

        self.color_transition_count += 1

        left_unlit = [self.unlit_color] * num_left_unlit
        left_lit = [self.lit_color] * num_left_lit
        right_lit = [self.lit_color] * num_right_lit
        right_unlit = [self.unlit_color] * num_right_unlit

        mapping = left_unlit + left_lit + right_lit + right_unlit
        device_display = ''.join([' ' if x != self.lit_color else '*' for x in mapping])

        print(f'dis [{device_display}]')
        print("vol " + ("-" * self.audio_volume) + "|")
        print("avg " + (" " * self.average_volume) + "|")
        print("mid " + (" " * self.current_center_offset) + "|")
        print(f'color {self.current_color} {self.lit_color}')
        print(f'bcolor {self.background_color} {self.unlit_color}')

        return mapping


    def __get_gradient_color_mapping(self):
        '''uses the gradient argument to pick colors based on the location of each segment of the gradient'''
        pass

    def __get_palette_color_mapping(self):
        '''uses the palette argument to assign colors based on a static list of colors'''
        pass