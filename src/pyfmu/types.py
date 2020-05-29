"""Contains definitions for common types used throughout the library."""

from pathlib import Path
import os
from typing import Union, Any, Protocol


"""A path represented either by a path object or a platform specific string."""
AnyPath = Union[str, os.PathLike]
os.PathLike
