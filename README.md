# CRFSim

## CRFV2_OOP
Primary simulation module. 
Runs through a time period, and, on each nanosecond, determines outputs, values, etc.

Contains 4 classes (for now) - GPTPGenerator, SourceMClk, CSGen and CLKDIV.

#### GPTPGenerator
Primary class. Does the iteration and calls the other modules (with the exception of CLKDIV, which is called by the CSGen module.)
#### SourceMClk
Generates a 48kHz "master" clock. May substitute this out for the generate_data script, and just access known timestamps through an array.
#### CSGen
Implementation of the CS2000 controlling hardware and clock correction logic.   
Implements a NCO to control the OCW to the CS2000.   
Implements a "clock correction" section for whatever clock correction algorithm is being used.
#### CLKDIV
Implements the CS2000.  
Reads in the OCW and determines the scaled outputs. Generates the output wave to be fed back in to CSGen for correction.