"""
Attempt at an OOP solution for the Rev2 CR Algorithm
"""

from queue import Queue


# The mock gPTP module
# this is going to be responsible for controlling everything - the "top level module"
class GPTPGenerator:
    current_value = 0

    def __init__(self):
        self.rxfifo = Queue()
        self.txfifo = Queue()

    def run(self, duration_nanoseconds):
        # Instantiate all the objects
        sourcecmclk = SourceMClk()
        csgen = CSGen()
        # Run the simulation
        for i in range(duration_nanoseconds+1):
            self.current_value += 1
            # print("The gPTP time is {}".format(i))
            # Call all relevant functions
            sourcecmclk.trigger(i)
            csgen.ocw_control(i)
        print("Finished simulation at {}".format(i))


# The Source media clock
class SourceMClk:
    base_freq = 48000
    base_period = 1/base_freq*pow(10, 9) # convert to nS

    def __init__(self):
        self.state = 0

    def trigger(self, gptp_time):
        if gptp_time % int(self.base_period) == 0:
            self.state = not self.state
            print("{} - Toggling source mclk".format(gptp_time))


# Module responsible for creating the output/control wave to the CS2000
class CSGen:
    threshold = 1302

    def __init__(self):
        self.state = 0
        self.count_to = 12499  # the value the CSGen must count to
        self.local_count = 0
        self.local_count_scale = 1  # How many times slower is the CS2000 driver module than the gPTP module?
        self.generated_timestamp = 0  # The most recent local timestamp

    def ocw_control(self, gptp_time):
        # increase local count by a related amount
        # TODO: Cater for self.local_count_scale here
        self.local_count = self.local_count + 1

        # this will control the o/c wave
        if self.local_count == self.count_to:
            print("{} - Toggling OCW".format(gptp_time))
            self.local_count = 0
            self.state = not self.state

            # if it's a rising edge, we need to call the clk_div
        pass

    def compare(self, source_mclk_timestamp):
        # this will run comparisons between the received TS and the generated gPTP timestamp
        if source_mclk_timestamp == self.generated_timestamp:
            # They're an exact match! We're good!
            # Unlikely to happen but we may as well cater for this here
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


# Takes the CS2000 OCW, multiplies it up a bunch, and gives us a 48khz out
# This STILL NEEDS TO DEPEND ON GPTP TIME! Perhaps an "is active" flag?
class CLK_DIV:
    multiplier = 24756
    output_freq = 48000
    output_period = 1 / output_freq * pow(10, 9)  # convert to nS


    def __init__(self):
        pass

    def activate(self, g):
        for i in range(multiplier+1):
            if i % output_period == 0:


if __name__ == '__main__':
    sim = GPTPGenerator()
    sim.run(99999)
