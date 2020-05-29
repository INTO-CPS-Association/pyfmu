import pytest

from .utils import get_all_examples, ExampleArchive
from pyfmu.builder import validate_fmu


def test_validate_non_existent_tool(tmpdir):
    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:
            with pytest.raises(ValueError):
                validate_fmu(archive.root, tools=["non existing"])
