"""Contains definitions for types that are not specific for FMI2 and FMI3."""

import os
from typing import Union


"""A path represented either by a path object or a platform specific string."""
AnyPath = Union[str, os.PathLike]
