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


def rev1(local_timestamp, rx_timestamp, prev_state):
    """
    The first attempt.
    This method requires a FIFO queue on the generated clock (currently unimplemented)
    :return:
    """

    # CRF-22 in F.12 specifies timestamps must be within +-5% of the media sample period.
    # so for an "accurate" clock, we'll set threshold_a to be 5% of the period
    threshold_a = 1041  # 5% of the period in nS
    # TODO: Double check the value of threshold_b
    # we're generating TS every 160 MClk. That means the greatest a difference can be is halfway between timestamps
    # Should threshold_b, which decides when another Timestamp is fetched, be 50% of the difference between timestamps?
    threshold_b = 1666666  # period of Mclk in nS * 80, rounded down
    difference = rx_timestamp- local_timestamp
    correction = 0
    to_log = []

    if -threshold_a <= difference <= threshold_a:
        state = State.DIFF_MATCH
    elif threshold_a < difference <= threshold_b:
        state = State.DIFF_GT
        correction = int(difference / 160 / 3.3)
    elif -threshold_b <= difference < -threshold_a:
        state = State.DIFF_LT
        correction = int(difference / 160 / 3.3)
    elif difference > threshold_b:
        state = State.DIFF_MGT
    elif difference < -threshold_b:
        state = State.DIFF_MLT
    else:
        state = State.DIFF_ERROR

    if prev_state != state:
        to_log = [["src_ts", rx_timestamp], ["gen_ts", local_timestamp], ["delta", difference], ["result", correction],
                  ["state", state]]

    return correction, state, to_log


def rev2(local_timestamp, rx_timestamp, prev_state):
    """
    Here we only care about a sample if it's within a "measurement window", which is smaller than 0.5T in either direction
    We assume that samples outside of this window are of no concern to us, and we ignore them

    The difference is calculated over the amount of time between sampled timestamps.
    As we only have timestamps with 160 interval to deal with
    - A correction to count_to affects the outclock by 3.33nS
    - We need to distribute corrections over 160 cycles (the time between RX timestamps) ???
    - The max difference worth making is 3.33*80, as anything greater than, is greater than the comparison window
    - The correction should thus be diff/(3.33*160)
    - The comparison algorithm runs at 25MHz, or 40nS
    - 160*20833/40 = 83332

    """
    to_log = []
    state = None
    difference = rx_timestamp-local_timestamp
    # Thresh B is about half the mclk cycle. We have 48khz = 20833 nS, or 10416.6667
    thresh = int(20833/2)  # We choose this, as the balance will be found on the "other end"/ next timestamp

    if difference == 0:
        correction = 0
        state = State.DIFF_MATCH
    elif (difference < 0) and (difference >= -thresh):
        # RX > local, speed up by decreasing count_to
        state = State.DIFF_LT
        correction = int(difference / 160 / 3.33)
    elif (difference > 0) and (difference <= thresh):
        # local > RX, need to slow down by increasing count_to
        state = State.DIFF_GT
        correction = int(difference / 160 / 3.33)
    else:
        correction = 0
        state = State.DIFF_ERROR

    if state != prev_state:
        to_log = [["src_ts", rx_timestamp], ["gen_ts", local_timestamp], ["delta", difference], ["result", correction],
                  ["state", state]]

    return correction, state, to_log

