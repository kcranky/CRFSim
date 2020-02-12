"""
This version creates a separate 48kHz wave that would be recovered from timestamps
"""

count_to = 12490
threshold = 100
gPTP_time = 0
cs2k_count = 0
period_ocw = int(1/1000 * pow(10, 9))  # period of the output/control wave to the CS2000
count_48 = 0



def main(time):
    """
    Runs the relevant processes by using nS timing as a step through process
    :time: Expects a duration in seconds
    :return:
    """
    duration = int(time*pow(10, 9))
    print("Iterating for {} nanoseconds".format(duration))

    for i in range(duration):
        # 125 MHz = 8nS
        if i % 8 == 0:
            run_125()
        run_cs2k()
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
        else:
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
    global count_to
    global count_48
    global gPTP_time

    count_48 = count_48 + 1
    if count_48 == 160:
        print("160 event gPTP time {}".format(gPTP_time))
        count_48 = 0
    return


def run_cs2k():
    """
    If we have this method pull in the period of the control wave from 125mhz process,
    we can determine when the output waves should be

    Mock CS2000 and clock divider implementation
    Every time it's run, for each high clock, we generate clk_in * 24576
    That's then divided down by 512 to get an output.
    When the divided output goes high, run_48 is called
    :return:
    """

    global cs2k_count
    global period_ocw
    global gPTP_time

    # if gptp is a modulo of the amount of time in ns of the control wave, we can assume the wave is an output
    # the control wave period is given by (1/f)* 10^9
    if gPTP_time % int((1/1000)*pow(10, 9)) == 0:
        print("HI WE'RE HERE {} - {}".format(cs2k_count, gPTP_time))
        # we have an output from the CS2000!
        cs2k_count = cs2k_count + 1
        if cs2k_count == 512:
            print("CS2k process running")
            run_48()
            cs2k_count = 0
    return


if __name__ == "__main__":
    main(0.1)
