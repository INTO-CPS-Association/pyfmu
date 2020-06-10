
import sys, ctypes
from ctypes import c_char_p, c_int, byref, c_void_p, c_uint, c_double, c_char, CFUNCTYPE, c_size_t, Structure

import sys
from pathlib import Path


fmi2Component = c_void_p
fmi2ComponentEnvironment = c_void_p
fmi2FMUstate = c_void_p
fmi2ValueReference = c_uint
fmi2Real = c_double
fmi2Integer = c_int
fmi2Boolean = c_int
fmi2Char = c_char
fmi2String = c_char_p
fmi2Type = c_int
fmi2Byte = c_char

fmi2Status = c_int

fmi2OK      = 0
fmi2Warning = 1
fmi2Discard = 2
fmi2Error   = 3
fmi2Fatal   = 4
fmi2Pending = 5


fmi2CallbackLoggerTYPE = CFUNCTYPE(
    None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String
)
fmi2CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi2CallbackFreeMemoryTYPE = CFUNCTYPE(None, c_void_p)
fmi2StepFinishedTYPE = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2Status)


class fmi2CallbackFunctions(Structure):

    _fields_ = [('logger',               fmi2CallbackLoggerTYPE),
                ('allocateMemory',       fmi2CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi2CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi2StepFinishedTYPE),
                ('componentEnvironment', fmi2ComponentEnvironment)]

prefix = {"win32": ""}.get(sys.platform, "lib")
extension = {"darwin": ".dylib", "win32": ".dll"}.get(sys.platform, ".so")


p = Path.cwd() / "pyfmu_wrapper" / "target" / "debug" / "pyfmu.dll"

lib = ctypes.cdll.LoadLibrary(p.__fspath__())

lib.print_str.argtypes = (c_char_p,)
lib.print_str.restype = None

lib.print_str_callback.argtypes = (c_char_p,c_void_p,)
lib.print_str_callback.restype = None

lib.fmi2Instantiate.argtypes = (
    fmi2String,fmi2Type,fmi2String,fmi2String, c_void_p, fmi2Boolean,fmi2Boolean)

lib.fmi2Instantiate.restype = None

print(lib.print_str("test".encode("utf-8")))
print(lib.print_str_callback("test".encode("utf-8"),None))



lib.fmi2Instantiate("a".encode("utf-8"),1,"".encode("utf-8"),"".encode("utf-8"),None,0,0)