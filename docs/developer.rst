#######################
Developer Documentation
#######################


====================
Repository Structure
====================

----
docs
----
Contains documentation, (the stuff you are reading right now), written in reStructuredText and build by Sphinx.



--------
examples
--------

Contains two folders: 1) projects, 2) exported.
The first of these contain examples of FMUs implemented in Python.
Invoking the invoking the command following command exports all projects as FMUs to the *exported* directory (in unzipped form).

.. code-block:: bash

   python build.py --export_examples 


-------------
pyfmu_wrapper
-------------

Contains source files for building and testing the wrapper, which is placed within each exported FMU.
The wrapper is a dynamic linked library which is loaded by the co-simulation tool when performing a co-simulation.
In turn it is this wrapper that executes the Python code that implements the FMUs dynamics.

The code is written in the RUST programming language, but is compatible with C's binary interface.

-----
tests
-----
Contains integration tests written in Python using the pytest test-framework.
Among other things these simulate and run checkers against the FMUs produced from the example projects.

========
Building
========

A utility script, *build.py*, for building the wrapper, running tests, and updating the resources is found in the root of the project.
Running the help command provides the options.

.. command-output:: python ../build.py --help



