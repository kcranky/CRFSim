"""
The goal of this file is to simulate the amount of pahse shift that an output wave might experience
from changes to the ocw in to the CS2000 module

Inputs: Count to
"""


def main():
    count_to = 20833
    ocw = 0

    for i in range(0, 10000000):
        if i == count_to:
            ocw = not ocw
            If the ocw is on a rising edge, trigger the cs2k process


The cs2k process will:
on a rising edge of the ocw,
generate a number of clock cycles based on the multiplier
on a certain count of those generated clock cycles, call the generated mclik function

the generated mclk function should, every 160 cycles, capture a gptp timestamp

That captured gPTP timestamp gets pushed back to the compare function


