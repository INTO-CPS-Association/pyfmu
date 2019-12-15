import fmpy
from os.path import join, dirname


fmu = join(dirname(__file__),"examples","multiplier")

fmpy.simulate_fmu(fmu)