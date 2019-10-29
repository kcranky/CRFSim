"""
Used to test implementations of CRF Recovery Logic

Obviously not perfect, as scheduling issues will corrupt timing.
Should (hopefully) be enough to validate implementation of logic in HDL.

Assumptions:
 - gPTP is a counter that increases by 1 for each nanosecond
 - gPTP is accessible at all nodes and is equal
"""

from generate_data import generate_timestamps as get_timestamps
import matplotlib.pyplot as plt
import datetime


def reconstruct(frequency, duration):
    toggle_ts = []
    out_arr = []
    print("generating timestamps")
    timestamps = get_timestamps(frequency, duration)
    print(timestamps)
    threshold = round((1/frequency)*pow(10,9)/2,0)
    print("Thres {}".format(threshold))
    print("running simulation")
    duration = duration*pow(10, 9)
    gPTP = 0
    out = 0
    ts_index = 0
    ts = timestamps[ts_index]
    while gPTP < duration:
        difference = gPTP - ts

        if (gPTP >= ts) and (difference < threshold):
            if out == 0:
                print("Toggling to 1 at gPTP {} for timestamp {}".format(gPTP, ts))
                print("Diff {}".format(difference))
                toggle_ts.append(gPTP)
                out_arr.append(1)
            out = 1
        else:
            if out == 1:
                print("Toggling to 0 at gPTP {} for timestamp {}".format(gPTP, ts))
                print("Diff {}".format(difference))
                toggle_ts.append(gPTP)
                out_arr.append(0)
            out = 0
        if (ts < gPTP) and (out == 0):
            print("Fetching next ts at gPTP {}".format(gPTP))
            ts_index += 1
            ts = timestamps[ts_index]
        # Move to next nanosecond
        gPTP += 1
    print(toggle_ts)
    print(out_arr)
    plot_square_wave(toggle_ts, out_arr)
    pass


def plot_square_wave(x_axis, y_axis):
    plt.plot(x_axis, y_axis, marker='d', color='blue', drawstyle='steps-post')
    plt.title("Waveform")
    plt.ylabel('Amplitude')
    plt.xlabel("Time")
    plt.savefig("waveform{:%d%m%Y%H%M}.png".format(datetime.datetime.now()))
    plt.show()
