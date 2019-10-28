def generate_timestamps(freq, duration):
    """
    Generate a list of timestamps for an expected duration at a specific frequency
    :param freq: frequency of the source oscillator
    :param duration: Duration in SECONDS
    :return:
    """
    period = 1/freq*pow(10, 9)
    timestamp = 0  # we can assume that the first clock will happen at t = 0
    ts_array = []
    while timestamp <= duration*pow(10, 9):
        # We round down to hold floats, this caters for non-exact divisions
        ts_array.append(round(timestamp))
        timestamp += period
    return ts_array
