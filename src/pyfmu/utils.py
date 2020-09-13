import json
import logging
import pathlib
import urllib
from pathlib import Path

from pkg_resources import resource_filename

logger = logging.getLogger(__file__)


def file_uri_to_path(file_uri: str, path_class=pathlib.PurePath) -> pathlib.Path:
    """Return the path corresponding a file-type URI.

    Args:
        file_uri: an file-type uri
        path_class: type of path

    Returns:
        path object referencing the specified uri
    """

    windows_path = isinstance(path_class(), pathlib.PureWindowsPath)
    file_uri_parsed = urllib.parse.urlparse(file_uri)
    file_uri_path_unquoted = urllib.parse.unquote(file_uri_parsed.path)
    if windows_path and file_uri_path_unquoted.startswith("/"):
        result = path_class(file_uri_path_unquoted[1:])
    else:
        result = path_class(file_uri_path_unquoted)
    if result.is_absolute() == False:
        raise ValueError(
            f"Invalid file uri {file_uri} : resulting path {result} not absolute".format()
        )
    return result
