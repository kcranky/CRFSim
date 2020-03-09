"""
This file should contain various potential recovery algorithms for testing, validation and comparison.

Input values : current gPTP time, local_timestamp, rx_timestamp
Return 2 values: Amount to shift CSGen by, and what to do with the RX and TX timestamps

return shifted, what_to_do

where what to do is an enum (see below)

"""

import enum


class State(enum.Enum):
    DIFF_MATCH = 0
    DIFF_LT = 1
    DIFF_MLT = 2
    DIFF_GT = 3
    DIFF_MGT = 4
    DIFF_ERROR = 5


def rev1(gptp_time, local_timestamp, rx_timestamp, logfile, prev_state):
    """
    The first attempt.
    We get a difference, then
    :return:
    """

    # CRF-22 in F.12 specifies timestamps must be within +-5% of the media sample period.
    # so for an "accurate" clock, we'll set threshold_a to be 5% of the period
    threshold_a = 1041  # 5% of the period in nS
    # TODO: Double check the value of threshold_b
    # we're generating TS every 160 MClk. That means the greatest a difference can be is halfway between timestamps
    # Should threshold_b, which decides when another Timestamp is fetched, be 50% of the difference between timestamps?
    threshold_b = 1666666  # period of Mclk in nS * 80, rounded down
    clock_shift = 0
    difference = local_timestamp - rx_timestamp

    if -threshold_a <= difference <= threshold_a:
        state = State.DIFF_MATCH
        clock_shift = 0
        if prev_state != state:
            logfile.write(
                "{}, [-A..A], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif threshold_a < difference <= threshold_b:
        state = State.DIFF_GT
        if prev_state != state:
            # TODO: slow down local clock by increasing count_to proportionally to the difference
            clock_shift = 1
            logfile.write(
                "{}, (A..B], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif difference > threshold_b:
        state = State.DIFF_MGT
        if prev_state != state:
            logfile.write(
                "{}, (B..inf], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif -threshold_b <= difference < -threshold_a:
        state = State.DIFF_LT
        if prev_state != state:
            # do a correction to speed up local clock by making count_to smaller
            clock_shift = -1
            logfile.write(
                "{}, [-B..-A), {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif difference < -threshold_b:
        state = State.DIFF_MLT
        if prev_state != state:
            logfile.write(
                "{}, [-inf..-B), {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    else:
        state = State.DIFF_ERROR
        if prev_state != state:
            logfile.write("Donkey\n")
            logfile.write("{}, {}-{}={}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    return clock_shift, state


def rev2():
    return

# etc
