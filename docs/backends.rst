########
Backends
########

PyFMU provides the implements several mechanisms, for executing the Python code inside an FMU, referred each referred to as an *Backend*.
Different backends have their own limitations and properties that may be useful when performing a co-simulation.

Switching between backends is acheived using the *config* command.





================
Embedded CPython
================
The most widely used implementation of the Python programming language is `CPython <https://github.com/python/cpython>`__, which, as the name suggests, is implemented in C.
It is possible to embed CPython in a program or library, in an approach referred to as `embedding python <https://docs.python.org/3.10/extending/embedding.html>`__.



.. warning::
    CPython application binary interface (ABI) may change in new releases of Python.
    Currently, the RUST bindings pyo3 are not built with the Python's `stable ABI <https://docs.python.org/3.10/c-api/stable.html>`__.
    This means that the FMUs are only guarenteed to be compatible with the version of Python present on the machine compiling the wrapper.

******************
Blocking Operation
******************

Blocking the calling thread indefintely in the slave code will usually cause the co-simulation to freeze.
This is due to the fact that it is the co-simulations calling thread the is being used to execute the Python code. 

In cases where the FMU does prolonged work that does not necessarily have to block, it is recommended to use a multiprocessing queue as shown in :ref:`example_liveplotting`.

=========================
Interpreter Message Queue
=========================

This backend spawn a new Python process for each instantiated slave. 
FMI function are invoked; and thier values returned, by sending messages thorugh a `ZMQ <https://zeromq.org/>`__-based message queue.




