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
        if prev_state != state:
            logfile.write(
                "{}, [-A..A], {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif threshold_a < difference <= threshold_b:
        state = State.DIFF_GT
        if prev_state != state:
            # TODO: slow down local clock by increasing count_to proportionally to the difference
            clock_shift = int(abs(difference / 213) / 40)
            logfile.write(
                "{}, (A..B], {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif difference > threshold_b:
        state = State.DIFF_MGT
        if prev_state != state:
            logfile.write(
                "{}, (B..inf], {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif -threshold_b <= difference < -threshold_a:
        state = State.DIFF_LT
        if prev_state != state:
            # do a correction to speed up local clock by making count_to smaller
            # 3.33 * 160 = ~213
            # We then further device by 40 to cater to convert nS to count
            clock_shift = int(abs(difference/213)/40)*-1
            logfile.write(
                "{}, [-B..-A), {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    elif difference < -threshold_b:
        state = State.DIFF_MLT
        if prev_state != state:
            logfile.write(
                "{}, [-inf..-B), {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    else:
        state = State.DIFF_ERROR
        if prev_state != state:
            logfile.write("Donkey\n")
            logfile.write("{}, {}-{}={}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

    return clock_shift, state


def rev2(gptp_time, local_timestamp, rx_timestamp, logfile, prev_state):
    """
    Here we only care about a sample if it's within a "measurement window", which is smaller than 0.5T in either direction
    We assume that samples outside of this window are of no concern to us, and we ignore them

    The difference is calculated over the amount of time between sampled timestamps.
    As we only have 160 timestamps to deal with
    - A correction to count_to affects the outclock by 3.33nS
    - We need to distribute corrections over 160 cycles (the time between RX timestamps)
    - The max difference worth making is 3.33*80, as anything greater than, is greater than the comparison window
    - The correction should thus be diff/(3.33*160)

    :param gptp_time:
    :param local_timestamp:
    :param rx_timestamp:
    :param logfile:
    :return:
    """
    difference = rx_timestamp-local_timestamp
    if abs(difference) > 0.5*20833:
        return None, 0
    elif difference <= int((0.5*20833)):
        # RX > local, speed up by decreasing count_to
        state = State.DIFF_LT
        correction = int(abs(difference / 213) / 40) * -1
        if state != prev_state:
            print(
                "{}, Speed up, {}, {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference, correction))
            return correction, state
    elif difference >= int((0.5*20833)):
        # local > RX, need to slow down by increasing count_to
        correction = int(abs(difference / 213) / 40)
        state = State.DIFF_GT
        if state != prev_state:
            print(
                "{}, Slow Down, {}, {}, {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference, correction))
            return correction, state



def rev3(gptp_time, local_timestamp, rx_timestamp, logfile, prev_state):
    return
# etc
