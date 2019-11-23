"""
This version creates a separate 48kHz wave that would be recovered from timestamps
"""

count_to = 12490
threshold = 100
gPTP_time = 0
cs2k_count = 0


def main(time):
    """
    Runs the relevant processes by using nS timing
    :time: Expects a duration in seconds
    :return:
    """
    duration = int(time*pow(10, 9))
    print("Iterating for {} nanoseconds".format(duration))
    for i in range(duration):
        # 125 MHz = 8nS
        if i % 8 == 0:
            run_125()
    return


def run_125():
    """
    Runs at 125MHz
    Creates a control wave to the CS2000
    :return:
    """
    global gPTP_time
    global count_to
    cnt_to = count_to
    cnt = 0
    output = 1  # we're assuming we start high

    gPTP_time = gPTP_time + 1
    if cnt == cnt_to:
        cnt = 0
        if output == 1:
            output = 0
        else :
            output = 1
            run_cs2k()
            cnt_to = count_to
    else:
        cnt = cnt + 1
    return


def run_48():
    """
    Triggered by the run_cs2k when appropriate when appropriate

    :return:
    """
    return


def run_cs2k(value):
    """
    Mock CS2000 and clock divider implementation
    Every time it's run, for each high clock, we generate clk_in * 24576
    That's then divided down by 512 to get an output.
    When the divided output goes high, run_48 is called
    :return:
    """
    print("CS2k process running")
    global cs2k_count
    for i in value * 24576:
        cs2k_count = cs2k_count + 1

    return


if __name__ == "__main__":
    main(0.01)
