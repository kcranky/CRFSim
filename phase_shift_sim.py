"""
The goal of this file is to simulate the amount of phase shift that an output wave might experience
from changes to the ocw in to the CS2000 module

Inputs: Count to
"""


from CRFv2_OOP import CSGen, CLKDIV
from queue import Queue

csgen = CSGen()

localfifo = Queue()

if __name__ == '__main__':
    for i in range(160*28333):
        csgen.ocw_control(i, localfifo)

        if i % 208330 == 0 and i > 0:
            print("{} - shifting -10".format(i))
            csgen.adjust_count_to(float(-10))

