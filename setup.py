
from setuptools import setup, find_packages
setup(
    name="pyfmu",
    version="0.0.1",
    packages=find_packages('src'),
    package_dir={'': 'src'},

    install_requires=["numpy", "pandas", "pytest", "Sphinx",
                      "recommonmark", "sphinx_rtd_theme", "sphinx-autoapi", "conan", "fmpy", "pyqtgraph", "scipy"],


    # resources needed by the CLI to generate and export 
    package_data={
        "pyfmu": [
            "resources/templates/*.j2",
            "resources/wrapper/binaries/*/*[.so|.dll]",
            "resources/validation/*"
        ]
    },
    include_package_data=True,

    python_requires='>=3',

    entry_points={'console_scripts': ['pyfmu=pyfmu.pyfmu_cli:main']}


)
# /usr/local/lib/python3.7/dist-packages/pyfmu/resources