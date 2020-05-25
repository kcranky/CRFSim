"""
Creates a look up table based on the difference value input
Avoids division on the FPGA

"""


def generate_values():
    """
    Generates a list of threshold values
    We know we can only work with a difference of up to half the period of the media clock.
    That's a gPTP value of about 20833. Rounding up to the nearest multiple of 8 gives us 20840.
    20840/2 = 10420. So we only need to calculate values for a difference up to and including 10420
    We know the output equation is correction = difference/160/3.3 = difference * (1/528)
    We also need to cater for rounding in results! So the returned value should cater for "half-steps" in that sense
    :return:
    """
    coefficient = 528
    upper_bound = 10420
    value = int(0.5*coefficient)
    thresholds = [value]
    while value < upper_bound:
        value = value + coefficient
        thresholds.append(value)
    return thresholds


def create_case_statement(values):
    string = "\t\tif diff <= to_unsigned({}, 64) then\n".format(values[0])
    string += "\t\t\treturn 0;\n"
    for i in range(len(values)-1):
        string += "\t\telsif diff <= to_unsigned({}, 64) then\n".format(values[i+1])
        string += "\t\t\treturn {};\n".format(i+1)
    string += "\t\telse\n"
    string += "\t\t\treturn 0;\n"
    string += "\t\tend if;\n"
    print(string)


if __name__ == "__main__":
    create_case_statement(generate_values())
