
from pyfmu.fmi2 import get_default_initial, validate_vc,Fmi2Causality, Fmi2Initial, Fmi2Variability

from pytest import raises

# check fmi2 spec page 48-49 for expected behavior

A = {'default' : Fmi2Initial.exact, 'possible': {Fmi2Initial.exact}}
B = {'default' : Fmi2Initial.calculated, 'possible': {Fmi2Initial.approx, Fmi2Initial.calculated}}
C = {'default' : Fmi2Initial.calculated, 'possible': {Fmi2Initial.exact, Fmi2Initial.approx, Fmi2Initial.calculated}}
D = {'default' : None, 'possible': {None}}
E = {'default' : None, 'possible': {None}} 


combinations = [
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.parameter, 'valid' : False},
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.calculatedParameter, 'valid' : False},
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.input, 'valid' : False},
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.output, 'valid' : True, 'initial' : A},
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.local, 'valid' : True, 'initial' : A},
    {'v': Fmi2Variability.constant, 'c': Fmi2Causality.independent, 'valid' : False},

    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.parameter, 'valid' : True, 'initial' : A},
    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.calculatedParameter, 'valid' : True, 'initial' : B},
    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.input, 'valid' : False},
    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.output, 'valid' : False},
    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.local, 'valid' : True, 'initial' : B},
    {'v': Fmi2Variability.fixed, 'c': Fmi2Causality.independent, 'valid' : False},

    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.parameter, 'valid' : True, 'initial' : A},
    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.calculatedParameter, 'valid' : True, 'initial' : B},
    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.input, 'valid' : False},
    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.output, 'valid' : False},
    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.local, 'valid' : True, 'initial' : B},
    {'v': Fmi2Variability.tunable, 'c': Fmi2Causality.independent, 'valid' : False},

    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.parameter, 'valid' : False},
    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.calculatedParameter, 'valid' : False},
    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.input, 'valid' : True, 'initial' : D},
    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.output, 'valid' : True, 'initial' : C},
    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.local, 'valid' : True, 'initial' : C},
    {'v': Fmi2Variability.discrete, 'c': Fmi2Causality.independent, 'valid' : False},

    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.parameter, 'valid' : False},
    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.calculatedParameter, 'valid' : False},
    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.input, 'valid' : True, 'initial' : D},
    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.output, 'valid' : True, 'initial' : C},
    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.local, 'valid' : True, 'initial' : C},
    {'v': Fmi2Variability.continuous, 'c': Fmi2Causality.independent, 'valid' : True, 'initial' : E}
]

def test_validate_vc():
    
    for c in combinations:
        va = c['v']
        ca = c['c']
        is_valid_expect = c['valid']
        ret = validate_vc(va,ca)

        if(is_valid_expect):
            assert(ret is None)
        else:
            assert(ret != None)

            


def test_get_default_initial():
    
    for c in combinations:
        
        va = c['v']
        ca = c['c']
        is_valid = c['valid']

        if(is_valid):
            default_actual = get_default_initial(va,ca)
            default_expect = c['initial']['default']
            
            assert(default_expect == default_actual)
