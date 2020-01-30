# python2fmu

A framework and utility program to support the use of Python3 code in Functional Mockup Units (FMUs).

# How does it work?

At a conceptual level an FMU can be thought of as a black box that converts a number of inputs into a number of outputs.

A simple example of this is an _adder_, which takes as input two numbers and produces the sum of these as its output.

<img src="documentation/figures/adder.svg" width="40%">

The FMU can be interacted with using several functions defined by the FMI specification. Some of the most essential of these are for getting values, setting values and advancing the simulation by taking a step. Using these three operations we can outline the process of simulating the adder as follows:

1. Initializing the FMU
2. Setting the value of the input A
3. Setting the value of the input B
4. Performing a step
5. Getting the value of output S

To reiterate, the FMI standard defines the interface that is implemented by FMUs. A key source of confusion how this interface may be _implemented_ in practice. In particular it may be unclear which programming languages can be used.

To clarify this it we may take a look at how the adder may look like as an FMU. Below is an example of what the file structure of the FMU may look like:

```
adder
|
+---binaries
|   +---win64
|   |   adder.dll
|   +---linux64
|   |   adder.so
|
+---resources
|   configuration.txt
|
+---sources
|   adder.c
|
|   modelDescription.xml
```

At a very rudementary level, a FMU is a shared object bundled with at configuration file _modelDescription.xml_, which declares its inputs, outputs and parameters.

- The shared object is what implements the behavior of the particular FMU. It does so by implementing the methods defined in the FMI specification.
- The model description acts as an interface for the simulation tools importing the FMU. It does so by expressing what inputs and outputs exist and what other capabilities are available.

It is important to note that the standard does not dictate **HOW** the shared object implements the functionality.
As a result there are fundamentally two ways to implment an FMU.

### **Compiled FMU**

The FMU is written in a compiled language that is capable of producing a shared object such as C. In addition to the specification itself, the standard is also shipped a number of C header files.
Implementing the headers in C makes it possible to compile the shared object as illustrated below:

<img src="documentation/figures/compiled_fmu.svg" width="25%">

Its important to emphasize that, even though C is the "favored" language, it is still possible to use any other language, as long as the resulting shared object is ABI compatible.

### **Wrapper FMU**

In addition to the document defining the standard, a number of C header files are available which declares the functions which must be implemented:

- fmi2getXXX :
- fmi2setXXX :
- fmi2dostep :

<img src="documentation/figures/python_wrapper.svg" width="70%">

# Prerequisites

## [Conan](https://docs.conan.io/en/latest/)

```bash
pip3 install conan
```

## [pytest](https://docs.pytest.org/en/latest/contents.html)

```
pip3 install pytest
```

## [CMake](https://cmake.org/download/)

Cross platform build system used to build the binaries that serves as wrappers for the Python scripts.

Linux using package manager:

```bash
sudo apt install cmake
```

Linux building from source:

1. download sources

**Note that the CMake scripts requires atleast version 3.10 of CMake**. This specific version is arbitrarily selected at the time.

# Usage

The utility program py2fmu provides

```bash
python3 py2fmu generate -p Adder
```

# FMI Support

Currently, only FMI2 is supported.

Support for FMI1 is **NOT** planned.

Support for FMI3 **is** planned.
