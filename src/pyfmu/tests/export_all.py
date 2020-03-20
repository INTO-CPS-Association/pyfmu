"""Export all example projects as FMUs to folder named exported
"""


from pathlib import Path

import tqdm

from pyfmu.tests import get_example_project, get_all_examples, get_example_directory

from pyfmu.builder.export import export_project
from pyfmu.builder.generate import PyfmuProject


def export_all():
    for name in get_all_examples():

        p = get_example_project(name)

        outdir = get_example_directory().parent / 'exported' / name
        project = PyfmuProject.from_existing(p)
        export_project(project, outdir, overwrite=True)


if __name__ == "__main__":

    export_all()
