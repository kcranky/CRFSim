"""
The goal of this file is to simulate the amount of phase shift that an output wave might experience
from changes to the ocw in to the CS2000 module

Inputs: Count to
"""
import data


def loopdeloop():
    inc = 3333333.33
    gen = 5000
    print("{},\t\t\t{},\t\t\t{},\t\t\t{}".format("NS", "SRC", "gen", "diff"))
    correction = 0

    for i in data.timestamps:
        diff = i-gen
        # don't check for threshold! We have no interim timestamps to validate here!
        correction = int(diff/160/3.33)
        nextgen = int(gen + inc + correction*3.33*160)
        gen = nextgen
        print(i, gen, diff, correction, nextgen)


if __name__ == "__main__":
    loopdeloop()
