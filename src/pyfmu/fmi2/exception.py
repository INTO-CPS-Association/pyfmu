
class SlaveError(Exception):
    """Common base class for errors related to  slaves."""
    pass


class SlaveAttributeError(SlaveError):
    """Unable to bind slave attribute to variable in the model."""
    pass


class SlaveConfigError(SlaveError):
    """Failure to read and parse slave configuration"""
    pass


class StartValueError(SlaveError):
    """Unable to determine start value of variable or start value is invalid"""
    pass


class InvalidVariableError(SlaveError):
    """A variable was created with an illegal combination of causality, variability, etc."""
    pass


class ModelDeclarationError(SlaveError):
    """Failed to extract information necessary to generate an description of the model."""
    pass
