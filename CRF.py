"""
Attempt 3
Let's go

Things that may need to be logged:
    - gptp_time (primary key)
    - src_ts - source timestamp used for comparison
    - gen_ts = generated timestamp used for comparison
    - count_to - count to value in the NCO
    - last_trigger - last trigger of the CS2000
    - cs2000difference - difference between current gptp value and last trigger
    - delta - the difference between TS in the recovery algorithm
    - result - the result of the correction algorithm. Negative means an increase in speed
    - shifting - the amount the NCO is being shifted by. Should match "result"

"""
import clock_recovery_algos as cra
from clock_recovery_algos import append_log as append_log
import data
from datetime import datetime
import os
import csv
import matplotlib.pyplot as plot


class GPTPSOURCE:
    def __init__(self, runtime, offset):
        now = datetime.now()
        self.simtime = now.strftime("%Y-%m-%d-%H-%M-%S")

        self.runtime = runtime
        self.genclk = []
        self.log = {}
        self.all_fields = [
            # primary gptp time, flag for generated mclk
            'gptp_time', 'genclk_out',
            # CS2000 control details
            'count_to', 'last_trigger', 'cs2000difference', 'F out',
            # Algorithm correction details
            'src_ts', 'gen_ts', 'delta', 'result',  'state',
            # Details from the shifting method
            'correction', 'shifting']

        # Instantiate all objects
        self.cs2000 = CLKDIV(self.log, self.genclk, offset)
        self.csgen = CSGEN(self.log, self.cs2000)

    def run(self):
        # Instantiate all objects
        # source_clock = SOURCEMCLK(self.srcclk)
        print("Starting Simulation")
        try:
            for i in range(0, self.runtime):
                # Devices that need to run constantly
                self.cs2000.generate_clock(i)
                # Devices that run on 25MHz
                if i % 40 == 0:
                    self.csgen.ocw_control(i)
                    self.csgen.correction_algorithm(i)
        except KeyboardInterrupt:
            print("Keyboard interrupt.")
        else:
            print("Simulation complete.")

    def save_log_file(self, log_fields):
        print("Saving Logfile")
        logname = "dataout/{}_CRFLog.csv".format(self.simtime)
        with open(logname, "w", newline="") as f:
            w = csv.DictWriter(f, log_fields)
            w.writeheader()
            for k, d in sorted(self.log.items()):
                tmp = {'gptp_time': k}
                for key in d:
                    if key in log_fields:
                        tmp.update({key: d[key]})
                if len(tmp) > 1:  # we don't want to write blank gptp events
                    w.writerow(tmp)
        print("Logfile saved to {}".format(logname))

    def draw_plot(self, start, duration):
        print("Drawing Plot")
        figname = "dataout/{}_Waveform-{}-{}.png".format(self.simtime, start, (start + duration))
        # plot source clock
        x_src, y_src = cra.split_lists(data.sourceclock, start, duration)
        plot.plot(x_src, y_src, color='blue', drawstyle='steps-post', linewidth=0.25)

        # get the gen clock
        x_gen, y_gen = cra.split_lists(self.genclk, start, duration)
        plot.plot(x_gen, y_gen, color='red', drawstyle='steps-post', linewidth=0.25)

        # Adjust some settings
        plot.title("{}_Waveform".format(self.simtime))
        plot.ylabel("Output Value")
        plot.xlabel("Time (nS)")
        plot.xticks(x_src[::6], x_src[::6], rotation='vertical')
        ax = plot.gca()
        ax.grid(True)
        ax.set_aspect(1.0 / ax.get_data_ratio() * 0.15)
        # Save
        plot.savefig(figname, dpi=2400)
        plot.close()
        print("Plot saved to {}".format(figname))
        return


class CSGEN:
    """
    Responsible for output/control wave to CS2000
    Responsible for running the correction algorithm
    NB: These functions are only called every 40ns (25Mhz clk)
    """

    def __init__(self, log, cs2000):
        self.count_to = 12500
        self.local_count = -1  # On 0 we need it to be zero. So adding 1 will get it to 1 too soon, hence set to -1
        self.state = 1
        self.clock_div_module = cs2000
        self.recovery_state = None
        # Timestamp data
        self.timestamps = data.timestamps
        self.srcclk_index = 0  # keeps track of which master clock we're comparing to
        self.log = log

    def ocw_control(self, gptp_time):
        """
        Controls the OCW
        :param gptp_time:
        :return:
        """
        self.local_count = self.local_count + 1

        # this will control the o/c wave
        if int(self.local_count) == int(self.count_to):
            to_log = [["count_to", self.count_to]]
            append_log(self.log, gptp_time, to_log)
            self.local_count = 0

            # if it's a rising edge, we need to call the clk_div
            self.state = not self.state
            if self.state == 1:
                # self.count_to = 12500  # reset the NCO back to 48kHz
                self.clock_div_module.trigger_cs2000(gptp_time)

    def correction_algorithm(self, gptp_time):
        # determine which srcclk we're comparing to
        srcclk_ts = self.timestamps[self.srcclk_index]
        genclk_ts = self.clock_div_module.latest_ts

        # call the correction algorithm
        shift, rec_state, tlog = cra.rev2(genclk_ts, srcclk_ts, self.recovery_state)

        # make an adjustment to count_to
        if self.recovery_state != rec_state:  # we've changed state and hence need to update!
            tlog.append(["correction", True])
            if shift is not None:
                tlog.append(["shifting", shift])
                self.count_to = self.count_to + shift
                self.srcclk_index = self.srcclk_index + 1
            self.recovery_state = rec_state

        # Add details to the log
        append_log(self.log, gptp_time, tlog)


class CLKDIV:
    """
    - Mimics CS2000
    - Implements the divider
    """

    def __init__(self, log, genclk, offset):
        self.multiplier = 24576  # Multiplier on the CS2000
        self.last_trigger = 0 + offset
        self.output_freq = 48000
        self.output_period = 1 / self.output_freq * pow(10, 9)
        self.latest_ts = 0
        self.mclk_state = 0
        self.genclk = genclk
        self.log = log

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

        # For some reason, when this algorithm is called, we don't get the genclk called correctly
        rate = 1 / (difference / (1*pow(10, 9))) * self.multiplier
        self.output_freq = rate / 512.0
        self.output_period = 1 / self.output_freq * pow(10, 9)
        lst_trig = gptp_time - difference
        to_log = [["last_trigger", lst_trig], ["cs2000difference", difference], ["rate", rate],
                  ["F out", self.output_freq]]
        append_log(self.log, gptp_time, to_log)

    def generate_clock(self, gptp_time):
        comp_val = gptp_time - self.latest_ts  # TODO When is the right time to genclk? SWITCHED TO TRIGGER
        if int(comp_val % int(self.output_period / 2)) == 0:
            self.mclk_state = not self.mclk_state
            self.genclk.append([gptp_time, self.mclk_state * 0.95])  # multiply by 0.95 to distinguish on graph
            if self.mclk_state == 1:
                append_log(self.log, gptp_time, [["genclk_out", True]])
                self.latest_ts = gptp_time


if __name__ == "__main__":
    run_time = int(0.1 * pow(10, 9))  # seconds to nS
    genclk_offset = 5000
    sim = GPTPSOURCE(run_time, genclk_offset)
    sim.run()

    # Make directory in case it doesn't exist
    if not os.path.exists("dataout"):
        os.makedirs("dataout")

    fields = sim.all_fields.copy()
    # exclude = ["genclk_out"]
    # for f in exclude:
    #     fields.remove(f)
    sim.save_log_file(fields)
    # sim.draw_plot(7500000, 20833*200)
    sim.draw_plot(0, 20833 * 200)
    sim.draw_plot(20833 * 200, 20833*200)
