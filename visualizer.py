import numpy as np
import colorsys
import subprocess
from lifxlan.utils import RGBtoHSBK
import random
import json
import struct
import numpy as np
from scipy.fftpack import rfft
# import pylab as plb
# import matplotlib.pyplot as plt


class MicrophoneVisualizer():

    current_color = 'RED'
    background_color = 'RED'

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
        self.sampling_rate = kwargs.get('sampling_rate')
        self.chunk_size = kwargs.get('chunk_size')
        self.channels = kwargs.get('channels')
        self.mode = kwargs.get('mode', 'static')
        self.window_length = kwargs.get('window_length', 50)
        self.colors = {
            'RED': [65535, 65535, 65535, 9000],
            'ORANGE': [6500, 65535, 65535, 9000],
            'YELLOW': [9000, 65535, 65535, 9000],
            'GREEN': [16173, 65535, 65535, 9000],
            'CYAN': RGBtoHSBK((0, 255, 255), 9000),
            'BLUE': [43634, 65535, 65535, 9000],
            'PURPLE': [50486, 65535, 65535, 9000],
            'PINK': [58275, 65535, 47142, 9000],
            # light white poop color
            # 'WHITE': [58275, 0, 65535, 9000],
            # light white poop color
            # 'COLD_WHITE': [58275, 0, 65535, 9000],
            # 'GOLD': [58275, 0, 65535, 9000],
            'MAGENTA': RGBtoHSBK((255, 0, 255), 9000)
        }

        self.color_transition_interval = kwargs.get('color_transition_interval', 50)
        self.color_transition_count = 0
        self.background_color_percent = 0.07

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
        subprocess.call('clear')
        if data is None:
            print('no data received when calling on_data')
            return

        self.__get_frequency_data(data)

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

    def __get_frequency_data(self, data):
        unpacked_data = struct.unpack(str(self.chunk_size * self.channels) + 'h', data)
        rfft_data = rfft(unpacked_data)
        abs_fourier_transform = np.abs(rfft_data)
        power_spectrum = np.square(abs_fourier_transform)
        frequency = np.linspace(0, self.sampling_rate/2, len(power_spectrum))

        print(f'frq {len(frequency)} {frequency}')
        print(f'pwr {len(power_spectrum)} {power_spectrum}')

        # plt.plot(frequency, power_spectrum)

        # bands = {
        #     'frequency': frequency.tolist(),
        #     'power': power_spectrum.tolist()
        # }

        # with open('bands.json', 'w') as outfile:
        #     json.dump(bands, outfile)

        # plt.plot(frequency, power_spectrum)

    def get_color_mapping(self):
        return self.current_zones

    def __get_static_color_mapping(self):
        num_left_lit = int(self.beam_volume * self.center_zone_offset)
        num_right_lit = int(self.beam_volume * (self.num_addressable_zones - self.center_zone_offset))
        num_left_unlit = self.center_zone_offset - num_left_lit
        num_right_unlit = (self.num_addressable_zones - self.center_zone_offset) - num_right_lit

        # this whole color transition thing is garbage and is just for experimenting

        if self.color_transition_count >= self.color_transition_interval:
            self.color_transition_count = 0

            self.current_color = random.choice(list(self.colors.keys()))
            self.background_color = random.choice(list(self.colors.keys()))

        # self.color_transition_count += 1
        
        unlit_color = [x * self.background_color_percent for x in self.colors[self.background_color]]
        lit_color = self.colors[self.current_color]

        left_unlit = [unlit_color] * num_left_unlit
        left_lit = [lit_color] * num_left_lit
        right_lit = [lit_color] * num_right_lit
        right_unlit = [unlit_color] * num_right_unlit

        mapping = left_unlit + left_lit + right_lit + right_unlit
        device_display = ''.join([' ' if x[-1] != lit_color[-1] else '*' for x in mapping])

        print(f'dis [{device_display}]')
        print("vol " + ("-" * self.audio_volume) + "|")
        print("avg " + (" " * self.average_volume) + "|")
        print(f'color {self.current_color} {lit_color}')
        print(f'bcolor {self.background_color} {unlit_color}')

        return mapping


    def __get_gradient_color_mapping(self):
        '''uses the gradient argument to pick colors based on the location of each segment of the gradient'''
        pass

    def __get_palette_color_mapping(self):
        '''uses the palette argument to assign colors based on a static list of colors'''
        pass