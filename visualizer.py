import numpy as np


class MicrophoneVisualizer():
    window_average = 0
    window = []
    peak = 0

    audio_volume = 0
    average_volume = 0
    average_volume_percent = 0.2

    # percent - 0 to 1
    beam_volume = 0

    def __init__(self, **kwargs):
        self.window_length = kwargs.get('window_length', 50)

        self.num_beams = kwargs.get('num_beams', 8)
        self.num_zones_per_beam = kwargs.get('num_zones_per_beam', 10)
        self.num_corner_pieces = kwargs.get('num_corner_pieces', 1)

        self.num_addressable_zones = (self.num_beams * self.num_zones_per_beam) + self.num_corner_pieces
        self.center_zone_offset = kwargs.get('center_zone_offset', (self.num_beams * self.num_zones_per_beam) / 2)


    def on_data(self, data = None):
        if data is None:
            print('no data received when calling on_data')
            return

        self.chunk_average = np.average(np.abs(data))
        chunk_average_peak = self.chunk_average * 2
        self.peak = chunk_average_peak

        # chunk average peak
        # window average peak

        # volume is chunk peak when compared to window peak

        if len(self.window) == self.window_length:
            self.window.pop(self.window_length - 1)

        self.window.insert(0, self.peak)
        self.window_average = np.average(self.window)

        self.audio_volume = int(50 * self.peak / 2 ** 16)
        self.average_volume = int(50 * self.window_average / 2 ** 16)
        self.chunk_average_volume = int(50 * self.chunk_average / 2 ** 16)

        self.beam_volume = round(self.chunk_average / self.window_average, 2)

        # more than (100 - X) percent of the current volume is over the average
        if self.beam_volume > 1:
            self.beam_volume = 1


    def get_zone_mappings(self):
        num_left_lit = int(self.beam_volume * self.center_zone_offset)
        num_right_lit = int(self.beam_volume * (self.num_addressable_zones - self.center_zone_offset))

        num_left_unlit = self.center_zone_offset - num_left_lit
        num_right_unlit = (self.num_addressable_zones - self.center_zone_offset) - num_right_lit

        left_unlit = np.zeros(num_left_unlit, dtype=int)
        left_lit = np.ones(num_left_lit, dtype=int)
        right_lit = np.ones(num_right_lit, dtype=int)
        right_unlit = np.zeros(num_right_unlit, dtype=int)

        return np.concatenate((left_unlit, left_lit, right_lit, right_unlit))