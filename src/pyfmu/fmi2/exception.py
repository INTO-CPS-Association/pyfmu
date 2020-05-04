class Fmi2Error(Exception):
    pass


class Fmi2InvalidVariableError(Fmi2Error):
    """A variable was declared variable that does not comply with the FMI2 specification."""

    def __init__(self, message: str, spec_reference: str):
        self.message = message
        self.specification_reference: str


class Fmi2ModelExtractionError(Fmi2Error):
    """Failed to extract information necessary to generate an description of the model."""

    pass
