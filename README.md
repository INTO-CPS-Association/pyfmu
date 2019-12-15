# PyFMU
A framework and set of utility programs to facility packaging of Python3 code as Functional Mockup Units (FMUs)

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