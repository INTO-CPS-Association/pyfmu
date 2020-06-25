![Build and update wrappers](https://github.com/INTO-CPS-Association/pyfmu/workflows/Build%20and%20update%20wrappers/badge.svg?branch=master)
[![PyPI version](https://badge.fury.io/py/pyfmu.svg)](https://badge.fury.io/py/pyfmu)
[![Documentation Status](https://readthedocs.org/projects/pyfmu/badge/?version=latest)](https://pyfmu.readthedocs.io/en/latest/?badge=latest)

# PyFMU

PyFMU is a library that allows FMUs to be implemented using in Python 3. Its goal is to enable rapid prototyping of a wide of FMUs for a wide range of use cases.

Its highlights include:

- Supports FMI 2.0.
- Write FMUs in high-level language.
- Use the extensive collection of standard and third party libraries.
- Model description automatically generated.
- Model can be changed without re-compilation.

## Supported Features

### Features

| Feature Name                         | Description | Supported | Notes                                                   |
| ------------------------------------ | ----------- | --------- | ------------------------------------------------------- |
| Instantiate multiple FMU per process |             | x         |                                                         |
| Custom memory allocators             |             |           | CPython does not allow dynamic selection of allocators. |
| User defined log categories          |             |           | Planned, not fully implemented.                         |

### Functions

While most of the commonly used FMI functions are used, some are currently not implemented.
Below is a table of defining which functions are currently safe to use.

| Functions                    | Supported | Notes                  |
| ---------------------------- | --------- | ---------------------- |
| fmi2DoStep                   | **x**     |                        |
| fmi2CancelStep               |           |                        |
| fmi2SetReal                  | **x**     |                        |
| fmi2GetReal                  | **x**     |                        |
| fmi2SetInteger               | **x**     |                        |
| fmi2GetInteger               | **x**     |                        |
| fmi2SetBoolean               | **x**     |                        |
| fmi2GetBoolean               | **x**     |                        |
| fmi2SetString                | **x**     |                        |
| fmi2GetString                |           | Safe, but leaks memory |
| fmi2SetDebugLogging          | **x**     |                        |
| fmi2SetupExperiment          | **x**     |                        |
| fmi2EnterInitializationMode  | **x**     |                        |
| fmi2ExitInitializationMode   | **x**     |                        |
| fmi2Reset                    | **x**     |                        |
| fmi2Terminate                | **x**     |                        |
| fmi2SetRealInputDerivatives  |           |                        |
| fmi2GetRealOutputDerivatives |           |                        |
| fmi2Terminate                | **x**     |                        |
| fmi2FreeInstance             | **x**     |                        |
| fmi2GetStatus                |           |                        |
| fmi2GetRealStatus            |           |                        |
| fmi2GetBooleanStatus         |           |                        |
| fmi2GetStringStatus          |           |                        |
| fmi2SerializeFMUstate        |           |                        |
| fmi2DeSerializeFMUstate      |           |                        |
| fmi2SerializedFMUstateSize   |           |                        |

## Installing

The project consists of two parts:

1. C/C++ shared library which acts which serves as an 'wrapper' around the Python code.
2. Set of tools for generating and exporting projects.

The wrapper is build using CMake as follows:

```bash
mkdir build
cd build
cmake ..
```

This will download external dependencies and try to locate Python 3 development headers.
Building the wrapper automatically copies it to the resources of the PyFMU tool.

To install the tools from source pip can be invoked from the root dir.

```bash
pip install -e.
```

## Usage

The library comes with a command line tool pyfmu which eases the creation of projects and the subsequent export as FMUs

As an example a two input Adder is used.

### Generating and implementing

To create a new project the _generate_ command is used:

```bash
pyfmu generate --path /someDir/Adder
```

This generates an empty project containing the necessary resources and configuration files.
By default a template of the slave class is generated. In this case a file _adder.py_ defining the class _Adder_ is created.

This subclasses the Fmi2Slave class which provides the methods necessary to define the FMU.

```Python
class Adder(Fmi2Slave):

    def __init__(self):
        # programatically register variables here
        ...

    def do_step(self, current_time: float, step_size: float) -> bool:
        return True

    ...
```

To define inputs, outputs and parameters the _register_variable_ function is used.
For a two input adder the inputs and outputs can be specified as:

```Python
def __init__(self):
    ...
    self.register_variable("s", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output)
    self.register_variable("a", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0)
    self.register_variable("b", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0)
```

Note that the variables MUST be defined either in the \_\_\_init\_\_\_ function or as part of a call chain resulting from it. This requirement is related to how model descriptions are extracted.

To implement the dynamics of the FMU the functions of the baseclass must be overwritten.
For the adder we define the _do_step_ and _exit_initialization_mode_ of the Adder class.

```Python
def exit_initialization_mode(self):
        self.s = self.a + self.b
        return True

def do_step(self, current_time: float, step_size: float) -> bool:
    self.s = self.a + self.b
    return True
```

It is not necessary to implement the **set_xxx** and **get_xxx** functions. By default these are mapped directly to instance variables.

### Exporting

To export an project as an FMU the **export** subcommand is used:

```bash
pyfmu export -p /someDir/Adder -o /myFMUs/Adder
```

The result of this command is an FMU containing the Python that was just written.

Under the hood a few things happen:

- Wrapper is copied to binaries
- Resources are copied into the archive
- A model description is generated.

The model description for the adder project looks like:

```XML
<?xml version="1.0" ?>
<fmiModelDescription author="" fmiVersion="2.0" generationDateAndTime="2020-02-23T09:30:00Z" generationTool="pyfmu" guid="221df7a6-36d3-41f7-bc35-8489663bb7ae" modelName="Adder" variableNamingConvention="structured">
   <CoSimulation modelIdentifier="pyfmu" needsExecutionTool="true"/>
   <ModelVariables>
      <!--Index of variable = "1"-->
      <ScalarVariable causality="output" initial="calculated" name="s" valueReference="0" variability="continuous">
         <Real/>
      </ScalarVariable>
      <!--Index of variable = "2"-->
      <ScalarVariable causality="input" name="a" valueReference="1" variability="continuous">
         <Real start="0"/>
      </ScalarVariable>
      <!--Index of variable = "3"-->
      <ScalarVariable causality="input" name="b" valueReference="2" variability="continuous">
         <Real start="0"/>
      </ScalarVariable>
   </ModelVariables>
   <ModelStructure>
      <Outputs>
         <Unknown dependencies="" index="1"/>
      </Outputs>
      <InitialUnknowns>
         <Unknown dependencies="" index="1"/>
      </InitialUnknowns>
   </ModelStructure>
</fmiModelDescription>
```

## Examples

See the tests/examples/projects folder.

## Setting Up the Development Environment

1. Clone this repo
2. Install rust and cargo (e.g., via rustup)
   1. Make sure to satisfy all requirements described by the installer (e.g., on windows, get the visual studio with MSVC, Windows 10 SDK, C++/CLI Support, etc...)
3. Open a terminal on the root of the repo (and make sure cargo is in the PATH), and run: `python build.py -ue --rust-tests --python-tests`
   1. This command will build pyfmu, export all examples, run all rust tests, and all python tests.
4. (Optional) Install pyfmu locally: `pip install -e .[dev]`

## Acknowledgements

- Lars Ivar Hatledal: For his implementation of PythonFMU which was the initial starting point for PyFMU.
