
from setuptools import setup, find_packages
setup(
    name="pyfmu",
    version="0.0.1",
    description='A set of tools for developing functional-mockup-units (FMUs) using the full capabilities of Python.',
    author='INTO-CPS Association',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    project_urls={
        'Bug Tracker': 'https://github.com/INTO-CPS-Association/pyfmu/issues',
        'Documentation': 'https://into-cps-application.readthedocs.io/en/latest/submodules/pyfmu/docs/index.html',
        'Source Code': 'https://github.com/INTO-CPS-Association/pyfmu'
    },

    install_requires=[
        'Jinja2'
    ],
    extras_require={

        "docs": ["Sphinx", "recommonmark", "sphinx_rtd_theme", "sphinx-autoapi"],
        "tests": ["numpy", "pandas", "pytest", "fmpy", "pyqtgraph", "scipy", "PyQt5"],
        "gui": []
    },

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
