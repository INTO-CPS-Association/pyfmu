from fmi import fmi2validation
from fmi.fmi2types import Fmi2Causality, Fmi2Initial, Fmi2Variability

def test_validate_vc():
    
    # check fmi2 spec page 48-49 for expected behavior
    cp = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.parameter)
    ccp = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.calculatedParameter)
    ci = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.input)
    co = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.output)
    cl = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.local)
    cid = fmi2validation.validate_vc(Fmi2Variability.constant, Fmi2Causality.independent)

    fp = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.parameter)
    fcp = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.calculatedParameter)
    fi = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.input)
    fo = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.output)
    fl = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.local)
    fid = fmi2validation.validate_vc(Fmi2Variability.fixed, Fmi2Causality.independent)

    tp = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.parameter)
    tcp = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.calculatedParameter)
    ti = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.input)
    to = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.output)
    tl = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.local)
    tid = fmi2validation.validate_vc(Fmi2Variability.tunable, Fmi2Causality.independent)

    dp = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.parameter)
    dcp = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.calculatedParameter)
    di = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.input)
    do = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.output)
    dl = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.local)
    did = fmi2validation.validate_vc(Fmi2Variability.discrete, Fmi2Causality.independent)

    ctp = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.parameter)
    ctcp = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.calculatedParameter)
    cti = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.input)
    cto = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.output)
    ctl = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.local)
    ctid = fmi2validation.validate_vc(Fmi2Variability.continuous, Fmi2Causality.independent)

    assert(cp != None)
    assert(ccp != None)
    assert(ci != None)
    assert(co is None)
    assert(cl is None)
    assert(cid != None)

    assert(fp is None)
    assert(fcp is None)
    assert(fi != None)
    assert(fo != None)
    assert(fl is None)
    assert(fid != None)

    assert(tp is None)
    assert(tcp is None)
    assert(ti != None)
    assert(to != None)
    assert(tl is None)
    assert(tid != None)

    assert(dp != None)
    assert(dcp != None)
    assert(di is None)
    assert(do is None)
    assert(dl is None)
    assert(did != None)

    assert(ctp != None)
    assert(ctcp != None)
    assert(cti is None)
    assert(cto is None)
    assert(ctl is None)
    assert(ctid is None)




