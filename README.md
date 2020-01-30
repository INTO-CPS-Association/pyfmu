# python2fmu
A framework and utility program to support the use of Python3 code in Functional Mockup Units (FMUs).

# How does it work?
The FMI standard specifies a set of functions 
```C
fmi2Status fmi2DoStep(fmi2Component c,
fmi2Real currentCommunicationPoint,
fmi2Real communicationStepSize,
fmi2Boolean noSetFMUStatePriorToCurrentPoint);
```


## Prerequisites

### [Conan](https://docs.conan.io/en/latest/)
```bash
pip3 install conan
```

### [pytest](https://docs.pytest.org/en/latest/contents.html)
```
pip3 install pytest
```

### [CMake](https://cmake.org/download/)
Cross platform build system used to build the binaries that serves as wrappers for the Python scripts.

Linux using package manager:
```bash
sudo apt install cmake
```



Linux building from source:

1. download sources

**Note that the CMake scripts requires atleast version 3.10 of CMake**. This specific version is arbitrarily selected at the time.

## Usage

The utility program py2fmu provides

```bash
python3 py2fmu generate -p Adder 
```
