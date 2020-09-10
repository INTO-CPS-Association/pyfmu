import json
import logging
import pathlib
import urllib
from pathlib import Path

from pkg_resources import resource_filename

logger = logging.getLogger(__file__)


def get_configuration(verify=True):
    """Returns configuration that controls the behavior of PyFMU such as the backends used to execute FMUs during runtime.

    The configuration is stored in a file named 'config.json' which is distributed by 'pkg_resources', and can be written to using
    the command

    ```
    pyfmu config
    ```

    """

    if verify:
        verify_configuration()

    config_path = Path(resource_filename("pyfmu", "resources/config.json"))

    with open(config_path, "r") as f:
        logger.debug(f"attempting to read configuration from file: '{config_path}'")
        return json.load(f)


def verify_configuration():
    """Asserts that PyFMU's global configuration file exists and is a consistent state

    In case the file is missing or damaged it can be restored using 'pyfmu config --reset'

    Raises:
        Exception: raised if the file is missing or in an inconsistent state
    """
    config_path = Path(resource_filename("pyfmu", "resources/config.json"))

    if not config_path.is_file():
        raise Exception(
            f"unable to locate PyFMU's configuration expected to be located at: '{config_path}'"
        )


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
