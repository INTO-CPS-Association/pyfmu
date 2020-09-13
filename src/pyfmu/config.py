import json
import sys
from pathlib import Path
from platform import system


from pkg_resources import resource_filename


def get_config_path() -> Path:
    return Path(resource_filename("pyfmu", "resources/config.json"))


def config_get_defaults():

    return {
        "backend.active": "interpreter_msgqueue",
        "log_stdout": False,
    }


def config_infer_os_specific():

    # for the embedded_cpython backend we need to explictly dlopen the python shared library,
    # otherwise extension modules such as numpy, tensorflow and similar will fail
    #
    # in the configuration we store the path to the stable abi version of the shared library.
    # On Windows the python3.dll acts as a redirect to the python3y.dll
    # On Linux it should be installed as both libpython3.so, and libpython3.y.so
    # https://www.python.org/dev/peps/pep-0384/
    #
    # Runtime issues will occur if the pyfmu wrapper (Rust code) is compiled against a different version
    # This can be fixed if pyo3 (Rust Rython bindings) start supporting the stable ABI
    # this appears to not be far off, see: https://github.com/PyO3/pyo3/pull/1152

    s = system()
    libname = {"Windows": "python3.dll", "Linux": "libpython3.so"}[s]
    libpython = (Path(sys.prefix) / libname).__fspath__()

    # we need interprocess communication. Windows do not support ipc
    protocol = {"Windows": "tcp", "Linux": "ipc"}[s]

    return {
        "backend.interpreter_msgqueue.executable": sys.executable,
        "backend.interpreter_msgqueue.protocol": protocol,
        "backend.embedded_cpython.libpython": libpython,
    }


def get_configuration():
    """Returns configuration that controls the behavior of PyFMU such as the backends used to execute FMUs during runtime.

    The configuration is stored in a file named 'config.json' which is distributed by 'pkg_resources', and can be written to using

    ```
    pyfmu config
    ```

    """

    with open(get_config_path(), "r") as f:
        return json.load(f)


def config_set_val(key: str, val: str):
    config = get_configuration()
    config[key] = val

    with open(get_config_path(), "w") as f:
        json.dump(config, f, sort_keys=True, indent=4)


def reset_config():

    defaults = config_get_defaults()
    guesses = config_infer_os_specific()

    assert not any(
        [k in guesses for k in defaults]
    ), "defaults and inferred information should be disjoint"

    config = {**defaults, **guesses}

    with open(get_config_path(), "w") as f:
        json.dump(config, f, sort_keys=True, indent=4)


def auto_configure():

    config = get_configuration()
    guesses = config_infer_os_specific()

    config = {**config, **guesses}

    with open(get_config_path(), "w") as f:
        json.dump(config, f, sort_keys=True, indent=4)
