"""
Used to test implementations of CRF Recovery Logic

Obviously not perfect, as scheduling issues will corrupt timing.
Should (hopefully) be enough to validate implementation of logic in HDL.

Assumptions:
 - gPTP is a counter that increases by 1 for each nanosecond
 - gPTP is accessible at all nodes and is equal
"""

from generate_data import generate_timestamps as get_timestamps


def reconstruct(duration, frequency):
    print("generating timestamps")
    timestamps = get_timestamps(frequency, duration)
    threshold = round(frequency/2,0)
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
                print("Toggling to high at gPTP {}".format(gPTP))
            out = 1
        else:
            if out == 1:
                print("Toggling to low at gPTP {}".format(gPTP))
            out = 0
        if (ts < gPTP) and (out == 0):
            ts_index += 1
            ts = timestamps[ts_index]
        # Move to next nanosecond
        gPTP += 1
    pass
