"""
A selection of useful functions for the simulation which assist in processing
"""


def get_verticals(log, x_list):
    temp_list = []
    for i in log:
        if int(i) < x_list[0]:
            pass
        elif int(i) >= x_list[-1]:
            break
        else:
            try:
                if log[i]['count_to_high']:
                    temp_list.append([int(i), 'green'])
            except KeyError:
                pass
            try:
                if log[i]["correction"]:
                    temp_list.append([int(i), 'yellow'])
            except KeyError:
                pass
    return temp_list


def append_log(log, gptp_time, items):
    try:
        log[gptp_time]
    except KeyError:
        log[gptp_time] = {}
    for i in items:
        log[gptp_time][i[0]] = i[1]


def split_lists(lst, start, duration):
    # TODO NEED TO ENSURE that it's a "TRUE" as a starting point
    index, arr = min(enumerate(lst), key=lambda x: abs(start - x[1][0]))
    end = index + int(duration / (20833 / 2))
    try:
        x_lst, y_lst = zip(*lst[index:end])
    except ValueError:
        print("No timestamp found. Simulation only supports up to 1s.")
        return [], []
    return x_lst, y_lst