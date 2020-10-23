.. .. pyfmu documentation master file, created by
..    sphinx-quickstart on Wed Feb 12 15:02:38 2020.
..    You can adapt this file completely to your liking, but it should at least
..    contain the root `toctree` directive.

########
Overview
########

PyFMU is a tool for developing *functional mock-up units* (FMUs) using Python.
The goal is to leverage Python's vast ecosystem of scientific packages to rapidly prototype FMUs, for use in FMI-based co-simulation.

PyFMU's main highlights are:

   * Implement models in *pure* Python with access to a vast amount of packages.
   * No need for compilation; OS specific issues are taken care of by framework.
   * Rapid iterations to models; modify and test code in Python using test suite and debugger.
   * Limited knowledge of FMI required; *model description* and packaging is automated.

If you want to learn by example take a look at the :ref:`sec_examples` section.

An obvious question is how the tool works?  Explaining this involves many technical details, but the gist of it is shown in :numref:`fig-workflow` 

.. _fig-workflow:
.. figure:: images/workflow.drawio.svg

   Depiction of how a Python class definition is transformed into an ready-to-use FMU.
   

.. toctree::
   :maxdepth: 2
   :hidden: 
   :caption: First Steps

   installing
   usage
   examples


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Advanced Topics

   configuration


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Technical Information

   autoapi/index

.. bibliography:: refs.bib
