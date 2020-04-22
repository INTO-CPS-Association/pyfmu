"""Contains definitions for common types used throughout the library."""

from pathlib import Path
from typing import Union

"""A path represented either by a path object or a platform specific string."""
AnyPath = Union[Path, str]
