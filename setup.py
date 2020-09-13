from setuptools import setup, find_packages


long_description = """
# PyFMU
PyFMU is a set of tools for developing functional-mockup-units (FMUs) using the full power of Python.

## Documentation
See the online documentation on how to use to tool and FMI in general see the INTO-CPS online documentation:

https://into-cps-application.readthedocs.io
"""

_extras_require = {
    "docs": [
        "Sphinx",
        "sphinx_rtd_theme",
        "sphinx-autoapi",
        "sphinxcontrib-bibtex",
        "sphinxcontrib-programoutput",
    ],
    "tests": [
        "numpy",
        "pandas",
        "OOModellingPython",
        "pytest",
        "tox",
        "fmpy",
        "pyqtgraph",
        "scipy",
        "PyQt5",
    ],
    "gui": [],
}
_extras_require["dev"] = _extras_require["docs"] + _extras_require["tests"]

setup(
    name="pyfmu",
    version="0.0.4",
    author="INTO-CPS Association",
    description="A set of tools for developing functional-mockup-units (FMUs) using the full capabilities of Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/INTO-CPS-Association/pyfmu",
    packages=find_packages("src"),
    package_dir={"": "src"},
    project_urls={
        "Bug Tracker": "https://github.com/INTO-CPS-Association/pyfmu/issues",
        "Documentation": "https://into-cps-application.readthedocs.io/en/latest/submodules/pyfmu/docs/index.html",
        "Source Code": "https://github.com/INTO-CPS-Association/pyfmu",
    },
    install_requires=["Jinja2", "lxml", "tqdm", "zmq"],
    extras_require=_extras_require,
    # resources needed by the CLI to generate and export
    package_data={
        "pyfmu": [
            "resources/templates/*.j2",
            "resources/wrapper/binaries/*/*[.so|.dll]",
            "resources/validation/*",
            "resources/config.json",
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={"console_scripts": ["pyfmu=pyfmu.pyfmu_cli:main"]},
)
