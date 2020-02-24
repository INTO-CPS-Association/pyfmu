"""Export all example projects as FMUs to folder named exported
"""


from pathlib import Path

import tqdm

from example_finder import get_example_project, get_available_examples

from pybuilder.builder.export import export_project
from pybuilder.builder.generate import PyfmuProject


if __name__ == "__main__":
    
    for name in get_available_examples():

        p = get_example_project(name)

        outdir = Path(__file__).parent / 'exported' / name
        project = PyfmuProject.from_existing(p)
        export_project(project,outdir)

        
        