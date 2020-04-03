"""
Attempt 3
Let's go
"""
import clock_recovery_algos as cra
import data
from datetime import datetime
import os


class GPTPSOURCE:
    def __init__(self):
        self.runtime = int(0.01*pow(10, 9))  # seconds to nS
        # self.srcclk = data.sourceclock  # If it is needed
        self.genclk = []
        # Instantiate all objects
        self.cs2000 = CLKDIV(self.genclk, 120)
        self.csgen = CSGEN(self.cs2000)

    def run(self):
        # Instantiate all objects
        # source_clock = SOURCEMCLK(self.srcclk)

        for i in range(0, self.runtime):
            # Devices that need to run constantly
            self.cs2000.generate_clock(i)
            # Devices that run on 25MHz
            if i % 40 == 0:
                self.csgen.ocw_control(i)
                self.csgen.correction_algorithm(i)

    def save_log_file(self, simtime, type, data):
        f = open("dataout/{}-CRF_{}.csv".format(simtime, type), "w+")
        for i in data:
            f.write("{}\n".format(i))
        f.close()

    def save_srcclk(self, simtime):
        d = ["gptp_time, mclk value"]
        for i in data.sourceclock:
            d.append("{},{}".format(i[0], i[1]))
        self.save_log_file(simtime, "srcclk", d)

    def save_genclk(self, simtime):
        d = ["gptp_time, mclk value"]
        for i in self.cs2000.genclk:
            d.append("{},{}".format(i[0], i[1]))
        self.save_log_file(simtime, "genclk", d)


class CSGEN:
    """
    Responsible for output/control wave to CS2000
    Responsible for running the correction algorithm
    NB: These functions are only called every 40ns (25Mhz clk)
    """
    def __init__(self, cs2000):
        self.count_to = 12500
        self.local_count = -1  # On 0 we need it to be zero. So adding 1 will get it to 1 too soon, hence set to -1
        self.state = 1

        self.clock_div_module = cs2000

        self.recovery_state = None

        # Timestamp data
        self.timestamps = data.timestamps
        self.srcclk_index = 0  # keeps track of which master clock we're comparing to

    def ocw_control(self, gptp_time):
        """
        Controls the OCW
        :param gptp_time:
        :return:
        """
        self.local_count = self.local_count + 1

        # this will control the o/c wave
        if int(self.local_count) == int(self.count_to):
            # print("{}, Reached {}".format(gptp_time, self.count_to))
            self.local_count = 0

            # if it's a rising edge, we need to call the clk_div
            self.state = not self.state
            if self.state == 1:
                self.count_to = 12500  # reset the NCO back to 48kHz
                self.clock_div_module.trigger_cs2000(gptp_time)

    def correction_algorithm(self, gptp_time):
        # determine which srcclk we're comparing to
        srcclk_ts = self.timestamps[self.srcclk_index]
        genclk_ts = self.clock_div_module.latest_ts

        # call the correction algorithm
        shift, rec_state = cra.rev2(gptp_time, genclk_ts, srcclk_ts, logfile, self.recovery_state)

        # make an adjustment to count_to
        if self.recovery_state != rec_state:  # we've changed state and hence need to update!
            print("{}, correcting, src={}, local={}".format(gptp_time, srcclk_ts, genclk_ts))
            if shift is not None:
                print("{}, shifting".format(gptp_time))
                self.count_to = self.count_to + shift
                self.srcclk_index = self.srcclk_index + 1
            self.recovery_state = rec_state


class CLKDIV:
    """
    - Mimics CS2000
    - Implements the divider
    """
    def __init__(self, genclk, offset):
        self.multiplier = 24576  # Multiplier on the CS2000
        self.last_trigger = 0 + offset
        self.output_freq = 48000
        self.output_period = 1 / self.output_freq * pow(10, 9)
        self.latest_ts = 0
        self.mclk_state = 0
        self.genclk = genclk
        self.ocw_log = ["gptp_time, last_trigger, diff, rate, output_freq"]

    def trigger_cs2000(self, gptp_time):
        """
        This is called by the CSGEN module
        Determines the output frequency of the "interim" wave based on the OCW
        Divides it by 512 to mimic the output module

        :param gptp_time: The current gPTP time
        :return:
        """
        difference = gptp_time - self.last_trigger
        self.last_trigger = gptp_time
        rate = 1 / (difference / (1 * pow(10, 9))) * self.multiplier
        self.output_freq = rate / 512.0
        self.output_period = 1 / self.output_freq * pow(10, 9)
        self.ocw_log.append("{}, {}, {}, {}, {}".format(gptp_time, gptp_time - difference, difference, rate, self.output_freq))

    def generate_clock(self, gptp_time):
        comp_val = gptp_time - self.last_trigger
        if int(comp_val % (self.output_period / 2)) == 0:
            self.mclk_state = not self.mclk_state
            self.genclk.append([gptp_time, self.mclk_state * 0.95])  # multiply by 0.95 to distinguish on graph
            if self.mclk_state == 1:
                self.latest_ts = gptp_time


if __name__ == "__main__":
    if not os.path.exists("dataout"):
        os.makedirs("dataout")
    now = datetime.now()
    sim_time = now.strftime("%Y-%m-%d-%H%M%S")
    logfile = open("dataout/{}-CRF_Sim.csv".format(sim_time), "w+")
    sim = GPTPSOURCE()
    sim.run()
    logfile.close()
