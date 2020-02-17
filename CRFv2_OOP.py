"""
Attempt at an OOP solution for the Rev2 CR Algorithm
"""

from queue import Queue


# The mock gPTP module
# this is going to be responsible for controlling everything - the "top level module"
class GPTPGenerator:
    current_value = 0

    def __init__(self):
        self.txfifo = Queue()
        self.localfifo = Queue()

    def run(self, duration_nanoseconds):
        # Instantiate all the objects
        sourcecmclk = SourceMClk()
        csgen = CSGen()
        # Run the simulation
        for i in range(duration_nanoseconds+1):
            self.current_value += 1
            # print("The gPTP time is {}".format(i))
            # Call all relevant functions
            sourcecmclk.trigger(i, self.txfifo)
            csgen.ocw_control(i, self.txfifo, self.localfifo)
            csgen.compare(self.txfifo, self.localfifo)
        print("Finished simulation at {}".format(i))


# The Source media clock
class SourceMClk:
    base_freq = 48000.0
    base_period = 1/base_freq*pow(10, 9) # convert to nS

    def __init__(self):
        self.state = 0
        self.event_count = 0

    def trigger(self, gptp_time, txfifo):
        # TODO : This isn't a perfect comparison, but it's the best we can do for now
        if int(gptp_time % self.base_period) == 0:
            self.state = not self.state
            # need to generate a timestamp every 160 cycles
            self.event_count = self.event_count + 1
            if self.event_count == 161:
                print("{} - 160th MClk".format(gptp_time))
                # Add to the tx buffer
                txfifo.put(gptp_time)
                self.event_count = 0


# Module responsible for creating the output/control wave to the CS2000
class CSGen:
    threshold = 1302

    def __init__(self):
        self.state = 0
        self.count_to = 500  # the value the CSGen must count to
        self.local_count = 0
        self.local_count_scale = 1  # How many times slower is the CS2000 driver module than the gPTP module?
        self.generated_timestamp = 0  # The most recent local timestamp

        self.clkdiv = CLKDIV()  # TODO: probably not the best place to put this?

    def ocw_control(self, gptp_time, txfifo, localfifo):
        # increase local count by a related amount
        # TODO: Cater for self.local_count_scale here
        self.local_count = self.local_count + 1

        # we need to check the gptp output every ns, so
        self.clkdiv.check(gptp_time, localfifo)

        # this will control the o/c wave
        if self.local_count == self.count_to:
            self.local_count = 0
            # if it's a rising edge, we need to call the clk_div
            if self.state == 0:
                # print("{} - Rising OCW".format(gptp_time))
                self.clkdiv.activate(gptp_time)
            self.state = not self.state

    def compare(self, txfifo, localfifo):
        pass
        # this will run comparisons between the received TS and the generated gPTP timestamp
        # if source_mclk_timestamp == self.generated_timestamp:
        #     # They're an exact match! We're good!
        #     # Unlikely to happen but we may as well cater for this here
        #     pass
        # elif source_mclk_timestamp > self.generated_timestamp+self.threshold:
        #     # Source clock is ahead of generated timestamp! Speed up!
        #     pass
        # elif source_mclk_timestamp < self.generated_timestamp+self.threshold:
        #     # source clock is behind generated timestamp! we should slow down
        #     pass
        # else:
        #     # ??? Way out of sync, shift the count to 90 degrees and try again?
        #     pass


# Takes the CS2000 OCW, multiplies it up a bunch, and gives us a 48khz out
# This STILL NEEDS TO DEPEND ON GPTP TIME! Perhaps an "is active" flag?
class CLKDIV:
    multiplier = 24756

    # TODO: Look at the maths behind the CS2k module that was documented in
    # The output wave is given by 24576*source wave
    # This "interim wave" is the divided down by 512 to generate a 48kHz wave
    def __init__(self):
        self.active = True
        self.state = 1
        self.last_trigger = 0
        self.output_freq = 48000.0

    def activate(self, gptp_time):
        self.active = True
        # we need to determine the rate at which the "activate" signals come in,
        # in order to multiply up and determine when to trigger
        difference = gptp_time - self.last_trigger
        self.last_trigger = gptp_time
        rate = difference* 24576 # this gives us how often we toggle the "iterim" wave
        self.output_freq = rate/512.0
        # print("time={}; diff={}; rate={}; mclk_rate={}".format(gptp_time, difference, rate, mclk_rate))

    def check(self, gptp_time, localfifo):
        # This function gets called every ns.
        if self.active:
            # if it is active, we need to see if the current gptp time is valid for it's multiplier
            if int(gptp_time % (1/self.output_freq*pow(10, 9))) == 0:
                print("{} Toggle generated Mclk".format(gptp_time))
                # We need to write to the Local buffer here
                localfifo.put(gptp_time)


if __name__ == '__main__':
    sim = GPTPGenerator()
    sim.run(99999)
