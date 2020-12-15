import random as rnd
import datetime as dt

class Timer:
    random_range = (1000, 9999)
    last_time = int(round(dt.datetime.today().timestamp() * 1000))
    diffs = []

    def __init__(self, **kwargs):
        self.name = str(kwargs.get(
            'name',
            int(self.random_range[0] + (rnd.random() * (self.random_range[1] - self.random_range[0])))
        ))
        self.window = kwargs.get('window', 20)
    
    def step(self):
        '''the next operation has happened, so increment the timer'''
        new_time = int(round(dt.datetime.today().timestamp() * 1000))
        self.diffs.append(new_time - self.last_time)
        self.last_time = new_time
        if len(self.diffs) > self.window:
            self.diffs = self.diffs[-self.window:]

    def is_limited(self, ops=20, ms=1000):
        '''returns whether this timer has been called more than the rate provided'''
        new_time = int(round(dt.datetime.today().timestamp() * 1000))
        interval = ms / ops

        time_to_next_op = self.last_time + interval - new_time
        print(f'{time_to_next_op} ms until next op')
        print(f'{new_time - self.last_time} ms since last op')

        return time_to_next_op >= 0
        
    def ops_per_ms(self, ms=1000):
        '''gets the number of operations per ms'''
        return int((ms / sum(self.diffs)) * len(self.diffs))

        