"""
Attempt at an OOP solution for the Rev2 CR Algorithm
"""


# The Source media clock
class SourceMClk:
    base_freq = 48000
    base_period = 1/base_freq*pow(10, 9) # convert to nS

    def __init__(self, output):
        self.state = 0

    def trigger(self, gPTP_time):
        if gPTP_time % int(self.base_period) == 0:
            self.state = not self.state


# The mock gPTP module
class GPTPGenerator:
    current_value = 0

    def __init__(self):
        pass

    def run(self, duration_seconds):
        for i in duration_seconds * pow(10, 9):
            self.current_value += 1


# Module responsible for creating the output/control wave to the CS2000
class CSGen:
    threshold = 1302

    def __init__(self):
        self.state = 0
        self.count_to = 12499 # the value the CSGen must count to
        self.local_count = 0
        self.local_count_scale = 1 # How many times slower is the CS2000 driver module than the gPTP module?
        self.generated_timestamp = 0 # The most recent local timestamp

    def ocw_control(self):
        # this will control the o/c wave
        if self.local_count == self.count_to:
            self.local_count = 0
            self.state = not self.state
        pass

    def compare(self, source_mclk_timestamp):
        # this will run comparisons between the received TS and the generated gPTP timestamp
        if source_mclk_timestamp == self.generated_timestamp:
            # They're an exact match! We're good!
            pass
        elif source_mclk_timestamp > self.generated_timestamp+self.threshold:
            # Source clock is ahead of generated timestamp! Speed up!
            pass
        elif source_mclk_timestamp < self.generated_timestamp+self.threshold:
            # source clock is behind generated timestamp! we should slow down
            pass
        else:
            # ??? Way out of sync, shift the count to 90 degrees and try again?
            pass
