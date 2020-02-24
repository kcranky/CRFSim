"""
This file should contain various potential recovery algorithms for testing, validation and comparison.

Input values : current gPTP time, local_timestamp, rx_timestamp
Return 2 values: Amount to shift CSGen by, and what to do with the RX and TX timestamps

return shifted, what_to_do

where what to do is an enum (see below)


"""

import enum

# CRF-22 in F.12 specifies timestamps must be within +-5% of the media sample period.
# so for an "accurate" clock, we'll set threshold_A to be 5% of the period
threshold_A = 1041  # 5% of the period in nS
# TODO: Double check the value of threshold_B
# we're generating TS every 160 MClk. That means the greatest a difference can be is halfway between timestamps
# Should threshold_B, which decides when another Timestamp is fetched, be 50% of the difference between timestamps?
threshold_B = 1666666  # period of Mclk in nS * 80, rounded down


class BuffersTodo(enum.Enum):
    FETCH_NONE = 0
    FETCH_LOCAL = 1
    FETCH_RX = 2
    FETCH_BOTH = 3


def rev1(gPTP_time, local_timestamp, rx_timestamp, logfile, FSM_state):
    """
    The first attempt.
    We get a difference, then
    :return:
    """
    global threshold_A
    global threshold_B
    todo = BuffersTodo.FETCH_NONE
    difference = local_timestamp - rx_timestamp

    if -threshold_A <= difference <= threshold_A:
        if self.FSM_state != 1:
            self.FSM_state = 1
            logfile.write(
                "{}, [-A..A], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))

        if txfifo.qsize() != 0:
            rx_timestamp = txfifo.get(1)
        if localfifo.qsize() != 0:
            local_timestamp = localfifo.get(1)  # get a value with a 1s timeout
    elif threshold_A < difference <= threshold_B:
        if self.FSM_state != 2:
            self.FSM_state = 2
            logfile.write(
                "{}, (A..B], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))
        # slow down local clock by increasing count_to proportionally to the difference
        todo = BuffersTodo.FETCH_BOTH

    elif difference > threshold_B:
        if self.FSM_state != 3:
            self.FSM_state = 3
            logfile.write(
                "{}, (B..inf], {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))
        todo = BuffersTodo.FETCH_RX

    elif -threshold_B <= difference < -threshold_A:
        if self.FSM_state != 4:
            self.FSM_state = 4
            logfile.write(
                "{}, [-B..-A), {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))
        # do a correction to speed up local clock by making count_to smaller
        todo = BuffersTodo.FETCH_BOTH

    elif difference < - threshold_B:
        if self.FSM_state != 5:
            self.FSM_state = 5
            logfile.write(
                "{}, [-inf..-B), {} , {}, {}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))
        todo = BuffersTodo.FETCH_LOCAL

    else:
        if self.FSM_state != 6:
            self.FSM_state = 6
            logfile.write("Donkey\n")
            logfile.write("{}, {}-{}={}\n".format(gptp_time, local_timestamp, rx_timestamp, difference))
    return 0, todo


def rev2():
    return

# etc
