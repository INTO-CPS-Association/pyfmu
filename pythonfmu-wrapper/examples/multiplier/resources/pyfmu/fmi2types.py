from enum import Enum


class Fmi2Causality(Enum):
    parameter = "parameter",
    calculatedParameter = "calculatedParameter",
    input = "input",
    output = "output",
    local = "local",
    independent = "independent"


class Fmi2DataTypes(Enum):
    real = "Real",
    integer = "Integer",
    boolean = "Boolean",
    string = "String"


class Fmi2Initial(Enum):
    exact = "exact",
    approx = "approx",
    calculated = "calculated"


class Fmi2Variability(Enum):
    constant = "constant",
    fixed = "fixed",
    tunable = "tunable",
    discrete = "discrete",
    continuous = "continuous"