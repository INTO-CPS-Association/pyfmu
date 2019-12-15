from fmpy import dump, simulate_fmu
import os
from os.path import join

def test_fmpy():
    
    working_dir = os.getcwd()
    
    fmu_path = join(working_dir,'generated','multiplier_export')
    

    dump(fmu_path)

    try:
        res = simulate_fmu(fmu_path)
    except Exception as e:
        test = e
        
    test = 10


    