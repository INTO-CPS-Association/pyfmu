##########
Installing
##########

PyFMU can be installed using pip or installing from source.
Installing using pip is the recommended approach:

.. code-block:: Bash

   pip install pyfmu


Alternatively, the package may be built from source. 
The first step of this is to obtain the source code from github:

.. code-block:: Bash

   git clone https://github.com/INTO-CPS-Association/pyfmu.git

The package may be installed in the system using pip by invoking:

.. code-block:: Bash

   pip install .

The recommended way to verify the installation and configuration of the tool is to run the `config`-subcommand with the following parameters.
Invoking the command should produce a result similar to the output shown below:

.. code-block:: bash

   pyfmu config --list
   backend.active=interpreter_msgqueue
   backend.embedded_cpython.libpython=.../python3.dll
   backend.interpreter_msgqueue.executable=../python.exe
   backend.interpreter_msgqueue.protocol=tcp
   log_stdout=False

.. note::

   During installation the tool will attempt to create a configuration by locating certain programs and inferring various pieces of information.
   For more information on the use of these variables and how to set them see :ref:`config`.