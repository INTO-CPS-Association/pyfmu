import ctypes
from ctypes import Structure, c_int, c_void_p, c_char_p, pointer, CFUNCTYPE, POINTER
from os.path import join


logger_prototype = CFUNCTYPE(
    c_void_p,  # return
    c_void_p,  # args
    c_char_p,
    c_int,
    c_char_p,
    c_char_p,
    c_void_p  # should really be va_list or ... but is not supported by python
)


allocateMemory_prototype = CFUNCTYPE(
    c_void_p,  # return
    c_int,  # size_t
    c_int,  # size_t
)


def py_fmi2CallbackLogger(componentEnv: str, instanceName: str, status: int, category: str, message: str, *args):
    print(message)


def py_allocateMemory(size, elems):
    print(f"fmu allocated {size},{elems}")


def freeMemory(ptr):
    print(f"freeing {ptr}")


def stepFinished(env_ptr, status):
    print(f"stepFinished")


env = None


class Fmi_Callbacks(Structure):
    _fields_ = [
        ("logger", logger_prototype),
        ("allocateMemory", allocateMemory_prototype),
        ("freeMemory", c_void_p),
        ("stepFinished", c_void_p),
        ("componentEnvironment", c_void_p)
    ]


lib = "build/wrapper/pyfmu.so"


instanceName = b"m"
cosim_type = 1
guid = b""

resource = b"examples/multiplier/resources/"
visible = False
loggingOn = False

if __name__ == "__main__":

    # bind python function to callback
    logger_callback = logger_prototype(py_fmi2CallbackLogger)
    allocateMemory_callback = allocateMemory_prototype(py_allocateMemory)
    callbacks = Fmi_Callbacks(logger_callback,allocateMemory_callback,None,None)

    try:
        # defining arg and ret types for validation in python before call
        fmu = ctypes.cdll.LoadLibrary(lib)
        fmu.fmi2Instantiate.argtypes = [
            c_char_p, c_int, c_char_p, c_char_p, POINTER(Fmi_Callbacks), c_int, c_int
        ]
        fmu.fmi2Instantiate.restype = c_void_p

        a = fmu.fmi2Instantiate(instanceName, cosim_type, guid,
                                resource, pointer(callbacks), visible, loggingOn)
        print(f"fmu instantiated with address: {a}")
    except Exception as e:
        print(f"whoops failed with exception: {e}")
