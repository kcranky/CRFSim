"""
Attempt at an OOP solution for the Rev2 Clock Recovery Algorithm

Keegan Crankshaw
February 2020

TODO:
    - Text/Readability changes
    - Better Class implementation
    - Better TLM implementation
    - implement different clock rates for the CS2000 vs full level simulation
        - i.e. have modules run at different clock rates as opposed to hardcoded values?
    - See if we can move away from global variables?
    - Implement the source clock separately as opposed to generating values on the fly as is currently done
    - Remove gen mclk buffer and just store the latest generated mclk value
"""

from queue import Queue
from datetime import datetime
import matplotlib.pyplot as plt
import clock_recovery_algos as cra
import os

# Arrays for plots
srcmclk = []
srcmclk_y = []
genmclk = []
genmclk_y = []


class GPTPGenerator:
    """
    Acts as the gPTP module and the source of time for all modules in the simulation
    """
    def __init__(self):
        self.txfifo = Queue()
        # self.localfifo = Queue()

    def run(self, duration_nanoseconds):
        global logfile
        sourcecmclk = SourceMClk()
        csgen = CSGen(offset=2500)
        # Run the simulation
        for i in range(duration_nanoseconds+1):
            # Call all relevant functions
            sourcecmclk.trigger(i, self.txfifo)  # see if we need to generate a mediaclock this nS
            if i % 40 == 0: # Processes on the 25Mhz clock
                csgen.ocw_control(i) # THIS IS BEING CALLED EVERY NS, BUT SHOULD BE SCALED FOR the 25MHZ clk
                csgen.compare(i, self.txfifo)  # moved this from main loop
        logfile.write("RXFIFO, {}\n".format(self.txfifo.qsize()))
        logfile.write("{}, Finished sim\n".format(i))

    # def save_localfifo(self):
    #     outfile = open("dataout/{}-CRFv2_OOP_LocalFifo.csv".format(simtime), "w+")
    #     outfile.write("gptp_time\n")
    #     for item in self.localfifo.queue:
    #         outfile.write("{}\n".format(item))
    #     outfile.close()

    def save_sourceclk(self, simtime):
        outfile = open("dataout/{}-CRFv2_OOP_MasterClk.csv".format(simtime), "w+")
        outfile.write("gptp_time\n")
        for i in range(len(srcmclk)):
            if srcmclk_y[i] == 1:
                outfile.write(str(srcmclk[i]))
        outfile.close()


# The Source media clock
# Validated 05/03/2020
class SourceMClk:
    """
    Source Media Clock generation
    TODO: May be able to do this separately and pull in a file for comparison, as opposed to generating dynamically
    """
    base_freq = 48000.0
    base_period = 1/base_freq*pow(10, 9)  # convert to nS

    def __init__(self):
        self.state = 0
        self.event_count = 0

    def trigger(self, gptp_time, txfifo):
        global srcmclk, srcmclk_y
        if int(gptp_time % (self.base_period/2)) == 0:
            self.state = not self.state
            srcmclk.append(gptp_time)
            srcmclk_y.append(self.state)
            # need to generate a timestamp every 160 cycles
            if self.state == 1:
                self.event_count = self.event_count + 1
                if self.event_count == 160:
                    self.event_count = 0
                    txfifo.put(gptp_time)


class CSGen:
    """
    This class is responsible for generating the output/control wave to the CS2000 (CLKDIV)
    """
    def __init__(self, offset=0):
        self.state = 1
        self.count_to = 12500  # the value the CSGen must count to
        self.rate_change = 40  # 1 x 25Mhz period
        self.local_count = 0
        # define current timestamp values
        self.rx_timestamp = None
        self.local_ts = None
        self.recovery_state = None
        self.offset = offset
        self.clkdiv = CLKDIV(offset)  # TODO: is this the best place to instantiate this?

    def ocw_control(self, gptp_time):
        self.local_count = self.local_count + 1

        # Handle the initial offset
        if self.offset != 0:
            if self.local_count >= self.offset:
                self.offset = 0
                self.local_count = 0
            else:
                return

        # this will control the o/c wave
        if int(self.local_count) == int(self.count_to):  # 40 is the amount of nS in one 25MHz Period # TODO REMOVED *40 AS IT IS CATERED FOR IN MAIN LOOP NOW
            print("Reached, {}".format(self.count_to))
            self.local_count = 0

            # if it's a rising edge, we need to call the clk_div
            self.state = not self.state
            if self.state == 1:
                # reset the NCO back to 48kHz
                self.count_to = 12500
                self.clkdiv.activate(gptp_time)


        # we need to check the gptp output every ns, so
        self.local_ts = self.clkdiv.check(gptp_time)

    def compare(self, gptp_time, txfifo):
        """
        Compares the received and generated timestamp
        :param gptp_time:
        :param txfifo:
        :return:

        TODO
            - Implement this without a local FIFO and see if performance changes?
            - Need to make a decision about checking timestamps based on their current gPTP timing.
            - For example, if I make a correction, from timestamps that happened a few ms ago,
                how long should I keep making that correction for?
        """
        global logfile
        # the first time we call this method, we need to initialise the timestamps
        # if localfifo.qsize() > 0 and txfifo.qsize() > 0 and self.local_timestamp is None:
        if txfifo.qsize() > 0:
            # self.local_timestamp = localfifo.get(1)  # get a value with a 1s timeout
            self.rx_timestamp = txfifo.get(1)

        if self.rx_timestamp is None:
            return

        # Algorithm 1
        # shift, rec_state = cra.rev1(gptp_time, self.local_timestamp, self.rx_timestamp, logfile, self.recovery_state)
        # if self.recovery_state in [cra.State.DIFF_MATCH, cra.State.DIFF_LT,  cra.State.DIFF_GT]:
        #     if txfifo.qsize() != 0:
        #         self.rx_timestamp = txfifo.get()
        #     if localfifo.qsize() != 0:
        #         self.local_timestamp = localfifo.get()
        # elif self.recovery_state == cra.State.DIFF_MLT:
        #     if localfifo.qsize() != 0:
        #         self.local_timestamp = localfifo.get()
        # elif self.recovery_state == cra.State.DIFF_MGT:
        #     if txfifo.qsize() != 0:
        #         self.rx_timestamp = txfifo.get()
        # elif self.recovery_state == cra.State.DIFF_ERROR:
        #     pass

        # Algorithm 2
        # we only call the shift recovery if we have mclks for comparison
        shift, rec_state = cra.rev2(gptp_time, self.local_ts, self.rx_timestamp, logfile, self.recovery_state)

        # Make sure we only shift once per state change
        if self.recovery_state != rec_state:
            if shift is not None:
                print("{}, shifting".format(gptp_time))
                self.adjust_count_to(shift)
            self.recovery_state = rec_state

        # Decide when to get the next RX timestamp
        # TODO this needs to be double checked
        if self.local_ts >= (self.rx_timestamp + (0.6*20833)):
            if txfifo.qsize() != 0:
                self.rx_timestamp = txfifo.get()

    def adjust_count_to(self, shift_value):
        # TODO: Because this is being adjusted by 160 increments
        #    We should likely have self.count_to = 12500 + shift_value
        self.count_to = self.count_to + shift_value
        # self.count_to = 12500 + shift_value
        print("Shifted by, {}, new, {}".format(shift_value, self.count_to))


class CLKDIV:
    """
    Responsible for mimicking the CS2000 and the clock divider module
    """
    multiplier = 24576

    def __init__(self, offset):
        self.state = 0
        self.last_trigger = 0 + offset
        self.output_freq = 48000.0
        self.output_period = (1/self.output_freq)*pow(10, 9)
        self.active = False
        self.latest_ts = 0

    def activate(self, gptp_time):
        """
        Determines the output frequency of the "interim" wave and devides it by 512 to mimic the output module
        :param gptp_time:
        :return:
        """
        self.active = True
        difference = gptp_time - self.last_trigger
        self.last_trigger = gptp_time
        rate = 1/(difference/(1*pow(10, 9))) * self.multiplier
        self.output_freq = rate/512.0
        self.output_period = 1/self.output_freq*pow(10, 9)
        # Enable this line to see changes to the output frequency in real time
        print("{}, last_trigger={}, diff={}, rate={}, output_freq={}".format(gptp_time, gptp_time-difference,
                                                                              difference, rate, self.output_freq))

    def check(self, gptp_time):
        """
        This function gets called every ns.
        We see if the current gPTP time would be a point at which the wave gets triggered
        :param gptp_time:
        :param localfifo:
        :return:
        """
        global genmclk, genmclk_y

        if self.active:
            comp_val = gptp_time - (self.last_trigger + 1)
            if int(comp_val % (self.output_period/2)) == 0:
                self.state = not self.state
                genmclk.append(gptp_time)
                genmclk_y.append(self.state*0.95)  # multiply by 0.5 to distinguish on graph
                if self.state == 1:
                    print("{}, mclk out".format(gptp_time))
                    self.latest_ts = gptp_time
                    # localfifo.put(gptp_time)
        return self.latest_ts


def plots():
    global srcmclk, srcmclk_y, genmclk, genmclk_y, simtime
    offset = len(srcmclk) - len(genmclk)  # Well let us start plotting from when the waves actually are worth observing
    duration = offset+50  # How long we want to plot for.

    plt.plot(srcmclk[offset:duration], srcmclk_y[offset:duration], color='blue', drawstyle='steps-post', linewidth=0.25)
    plt.plot(genmclk[:duration-offset], genmclk_y[:duration-offset], color='red', drawstyle='steps-post', linewidth=0.25)
    plt.title("Waveform-{}".format(simtime))
    plt.ylabel('Amplitude')
    plt.xlabel("Time")
    plt.xticks(srcmclk[offset:duration:6], srcmclk[offset:duration:6], rotation='vertical')
    plt.yticks([0, 1], [0, 1])
    ax = plt.gca()
    ax.grid(True)
    ax.set_aspect(1.0 / ax.get_data_ratio() * 0.15)
    plt.savefig("dataout/{}-waveform.png".format(simtime), dpi=2400)


if __name__ == '__main__':
    if not os.path.exists("dataout"):
        os.makedirs("dataout")
    now = datetime.now()
    simtime = now.strftime("%Y-%m-%d-%H%M%S")
    logfile = open("dataout/{}-CRFv2_OOP_Sim.csv".format(simtime), "w+")
    logfile.write("gptp_time, range, local_timestamp, rx_timestamp, difference\n")
    sim = GPTPGenerator()
    sim.run(int(28333*1600*3))
    # sim.run(28333*160)
    logfile.close()
    # sim.save_sourceclk(simtime)
    # sim.save_localfifo()
    plots()
