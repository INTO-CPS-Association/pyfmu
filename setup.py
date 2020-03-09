
from setuptools import setup, find_packages
setup(
    name="pyfmu",
    version="0.0.1",
    packages=find_packages('src'),
    package_dir={'': 'src'},

    install_requires=["numpy", "pandas", "pytest", "Sphinx",
                      "recommonmark", "sphinx_rtd_theme", "sphinx-autoapi", "cmake", "conan", "fmpy"],


    entry_points={'console_scripts': ['pyfmu=pybuilder.pyfmu:main']}


)
